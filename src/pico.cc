/**
 * @file pico.cc
 * @author Yi-Mu Chen
 * @brief Interface for picotech-PICOSCOPE used for SiPM data collection.
 *
 * @class PicoUnit
 * @ingroup hardware
 * @brief Interface for the picotech PICOSCOPE for data collection
 *
 * Here we are specializing the PICOSCOPE to the specific model used at UMD
 * (PS5234), and the operations needed for collecting SiPM/pulse-like data. The
 * main reference program used making this interface class can be found in the
 * official picotech [Github repository][pico-github].
 *
 * A big chuck of the PICO scope interface revolves round hte collection of
 * "rapidblocks", sets waveforms collected over multiple triggers, which speeds
 * up the available data aquisition rate of the picoscope. Most of the storage
 * classes in the PicoUnit class is creating machine side memory space to
 * receive the larger data blocks from the picscope unit.
 *
 * Notice that the timing spacing is explicitly initialized to be the smallest
 * time interval available (2ns) and explicitly hidden from the user.
 *
 * [pico-github]: https://github.com/picotech/picosdk-c-examples
 */

#include "logger.hpp"
#include "pico.hpp"
#include <libps5000/ps5000Api.h>

#include <chrono>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>
#include <thread>

static const std::string DeviceName = "PICODEV";

static const float inputRanges[PS5000_MAX_RANGES] = {
  10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000 };


/**
 * @brief Initializing the Picoscope interface
 *
 * Currently there is no what to specify the which device is being used by the
 * underlying driver. On the python level, there are ways to not initialize the
 * device based on the device path given, but that is currently the only method
 * to "change" the working device should such a requirement be needed.
 */
void
PicoUnit::Init()
{
  char errormessage[1024];
  if( device ){
    ps5000CloseUnit( device );
  }
  const auto status = ps5000OpenUnit( &device );
  if( status != PICO_OK ){
    sprintf( errormessage,
             "Cannot open picotech device (Error code: %d)",
             status  );
    throw device_exception( DeviceName, errormessage );
  }
  std::this_thread::sleep_for( std::chrono::seconds( 1 ) );

  // Setting up default settings
  SetVoltageRange( PS5000_CHANNEL_A, PS5000_100MV );
  SetVoltageRange( PS5000_CHANNEL_B, PS5000_100MV );
  SetTrigger( PS5000_EXTERNAL, RISING, 500, 0, 0 );

  // 0 delay, indefinite trigger wait time.
  std::this_thread::sleep_for( std::chrono::seconds( 1 ) );
  SetBlockNums( 5000, 100, 0 );
  FindTimeInterval();
}


/**
 * @{
 * @brief Abstraction for voltage range and voltage range settings
 */
int
PicoUnit::VoltageRangeMin() const
{
  return PS5000_100MV;
}


int
PicoUnit::VoltageRangeMax() const
{
  return PS5000_20V;
}


void
PicoUnit::SetVoltageRange( const int16_t channel, const int newrange )
{
  const static int16_t enable     = 1;
  const static int16_t dc_coupled = 1;
  char                 errormessage[1024];
  auto                 status = ps5000SetChannel( device,
                                                  (PS5000_CHANNEL)channel,
                                                  enable,
                                                  dc_coupled,
                                                  (PS5000_RANGE)newrange );
  if( status != PICO_OK ){
    sprintf( errormessage, "Error setting up channel (Error code:%d)", status );
    throw device_exception( DeviceName, errormessage );
  }
  range[channel] = newrange;
}


/** @} */

/**
 * @brief Trigger settings
 *
 * The channel, direction, analog trigger level (if applicable) , and delay
 * time, and the maximum trigger wait time needs to be all be provided.
 *
 * A few comments on the input:
 * - Despite only having 2 data channels, the external trigger channel is
 *   placed on channel "4". This is for compatibility with similar models in
 *   the picoscope product line.
 * - The ADC level input in this functions is in values of mV. It will
 *   automatically be translated to ADC values in this function.
 * - The trigger delay is units of 10 time steps (so 20ns in the default
 *   settings of the calibration system) As this is a very coarse settings that
 *   is difficult to reflect, no conversion will be provided for the delay
 *   settings.
 *
 * @param channel
 * @param direction
 * @param level
 * @param newdelay
 * @param maxwait
 */
void
PicoUnit::SetTrigger( const int16_t  channel,
                      const int16_t  direction,
                      const float    level,
                      const unsigned newdelay,
                      const int16_t  maxwait )
{
  static const int16_t enable   = 1;
  const int16_t        leveladc = channel ==
                                  PS5000_EXTERNAL ? ( level * PS5000_MAX_VALUE )
                                  / 20000 : ( level * PS5000_MAX_VALUE )
                                  / inputRanges[range[channel]];
  char errormessage[1024];

  auto status = ps5000SetSimpleTrigger( device,
                                        enable,
                                        (PS5000_CHANNEL)channel,
                                        leveladc,
                                        (THRESHOLD_DIRECTION)direction,
                                        newdelay,
                                        maxwait );
  if( status != PICO_OK ){
    sprintf( errormessage,
             "Error setting up trigger (Error code:%d)",
             status  );
    throw device_exception( DeviceName, errormessage );
  }

  // Storing information
  triggerchannel   = channel;
  triggerdirection = direction;
  triggerlevel     = level;
  triggerdelay     = newdelay;
  triggerwait      = maxwait;
}


/**
 * @brief Setting the number of captures for perform in a single lumi-block run,
 * as well as the number of samples to collected before and after the trigger
 * instance.
 *
 * Also resizes the arrays used for receive the block results.
 */
void
PicoUnit::SetBlockNums( unsigned ncaps, unsigned post, unsigned pre )
{
  char errormessage[1024];
  int  maxcapture;
  auto status = ps5000MemorySegments( device,
                                      ncaps,// Number of captures per rapid
                                            // block to store
                                      &maxcapture );
  status = ps5000SetNoOfCaptures( device, ncaps );
  if( status != PICO_OK ){
    sprintf( errormessage,
             "Error setting rapid block capture (Error code%d)",
             status );
    throw device_exception( DeviceName, errormessage );
  }
  if( post+pre > (unsigned)maxsamples ){
    sprintf( errormessage,
             R"(requested samples [%u+%u]greater than maximum allowed
             samples[%d], truncating to maximum)",
             pre,
             post,
             maxsamples );
    printwarn( DeviceName, errormessage );
    post = maxsamples-pre;
  }

  // Resizing capture buffer only if needed (reqesting more stuff)
  if( ncaptures < ncaps ){
    bufferA.resize( ncaps );
    bufferB.resize( ncaps );
    for( unsigned i = ncaptures; i < ncaps; ++i ){
      bufferA[i].reset( new int16_t[presamples+postsamples] );
      bufferB[i].reset( new int16_t[presamples+postsamples] );
      if( bufferA[i] == nullptr || bufferB[i] == nullptr ){
        sprintf( errormessage,
                 R"(Failed to initialize block memory buffer (%d/%d).
                 Maybe try smaller number of captures)",
                 i,
                 ncaptures );
        throw device_exception( DeviceName, errormessage );
      }
    }
    overflowbuffer.reset( new int16_t[ncaps] );
  }
  ncaptures = ncaps;
  if( presamples+postsamples < pre+post ){
    for( unsigned i = 0; i < ncaptures; ++i ){
      bufferA[i].reset( new int16_t[ pre+post ] );
      bufferB[i].reset( new int16_t[ pre+post ] );
      if( bufferA[i] == nullptr || bufferB[i] == nullptr ){
        sprintf( errormessage,
                 R"(Failed to initialize block memory buffer (%d/%d).
                 Maybe try smaller number of captures)",
                 i,
                 ncaptures );
        throw device_exception( DeviceName, errormessage );
      }
    }
  }
  presamples  = pre;
  postsamples = post;
}


/**
 * @brief Starting rapidblock collection.
 *
 * The function will exit as soon as the rapidblock is setup. The users can
 * check whether rapid block collection has completed (ready to have picoscope
 * memory be flushed to device) using the IsReady method.
 */
void
PicoUnit::StartRapidBlock()
{
  char errormessage[1024];
  auto status = ps5000RunBlock( device,
                                presamples,
                                postsamples,
                                timebase,// minimal temporal resolution
                                true,// enable oversampling.. ???
                                nullptr,// Not saving runtime information
                                0,// memory index to store information
                                nullptr,
                                nullptr// Using IsReady, don't need to set here
                                );
  if( status != PICO_OK ){
    sprintf( errormessage,
             "Error setting up run block (Error code:%d)",
             status );
    throw device_exception( DeviceName, errormessage );
  }
}


/**
 * @brief Check if rapidblock collection has completed.
 *
 * If yes, flush the data in the picoscope internal memory to device and return
 * true. Simple return false otherwise.
 */
bool
PicoUnit::IsReady()
{
  int16_t ready;
  ps5000IsReady( device, &ready );
  if( ready ){
    FlushToBuffer();
  }
  return ready;
}


/**
 * @brief Flushing the data in the picoscope internal memory to main device.
 */
void
PicoUnit::FlushToBuffer()
{
  uint32_t actualsamples = presamples+postsamples;
  int      status        = 0;
  char     errormessage[1024];
  for( unsigned block = 0; block < ncaptures; ++block ){
    status = ps5000SetDataBufferBulk( device,
                                      PS5000_CHANNEL_A,
                                      bufferA[block].get(),
                                      actualsamples,
                                      block );
    status = ps5000SetDataBufferBulk( device,
                                      PS5000_CHANNEL_B,
                                      bufferB[block].get(),
                                      actualsamples,
                                      block );
    if( status != PICO_OK ){
      sprintf( errormessage,
               "Error setting up data buffer (Error code:%d)",
               status );
      throw device_exception( DeviceName, errormessage );
    }
  }
  ps5000GetValuesBulk( device,
                       &actualsamples,
                       0,
                       ncaptures-1,// flush range
                       overflowbuffer.get()// overflow buffer
                       );
}


/**
 * @brief Suspending the main thread indefinitely until the rapid block
 * collection is complete. Notice that this flush the data to buffer when the
 * function exits.
 */
void
PicoUnit::WaitTillReady()
{
  while( !IsReady() ){
    std::this_thread::sleep_for( std::chrono::microseconds( 5 ) );
  }
  return;
}


/**
 * @brief Getting the raw readout results as a 16bit signed integer.
 */
int16_t
PicoUnit::GetBuffer( const int      channel,
                     const unsigned cap,
                     const unsigned sample ) const
{
  return channel == 0 ? bufferA[cap][sample] : bufferB[cap][sample];
}


/**
 * @brief Converting the ADC value to millivolts according to the current range
 * settings of a certain channel.
 *
 * Notice that the ADC value should be passed into this function as obtained
 * from the GetBuffer method, even if the last 8 bits of the GetBuffer method
 * is effectively redundent.
 */
float
PicoUnit::adc2mv( int16_t channel, int16_t adc ) const
{
  return adc * inputRanges[range[channel]] / PS5000_MAX_VALUE;
}


/**
 * @brief Printing the first 6 captures waveforms in a table on the screen.
 *
 * Very verbose method for debugging purposes. As this is used strictly for
 * debugging and the information is never stored, we will not use the official
 * logging library used for print the information
 */
void
PicoUnit::DumpBuffer() const
{
  static const unsigned maxcols      = 6;
  const unsigned        ncols        = std::min( ncaptures, maxcols );
  std::string           output_table = "";

  // Header line
  add_to_table( output_table, "%-7s | ", "Time" );
  for( unsigned j = 0; j < ncols; ++j ){
    add_to_table( output_table, "Capture:%-11d |", j );
  }
  add_to_table( output_table, "\n" );

  // Per channel line
  for( unsigned i = 0; i < presamples+postsamples; ++i  ){
    const int t = (int)i-(int)presamples;
    add_to_table( output_table, "%5dns | ", ( t * timeinterval ) );
    for( unsigned j = 0; j < ncols; ++j ){
      add_to_table( output_table,
                    "(%8.2f,%8.2f) |",
                    adc2mv( 0, GetBuffer( 0, j, i ) ),
                    adc2mv( 1, GetBuffer( 1, j, i ) ) );
    }
    add_to_table( output_table, "\n" );
  }

  printdebug( DeviceName, output_table );
}


/**
 * @brief Returning the specified capture within a the rapidblock buffer of the
 * specified channel as a hex string.
 *
 * Notice that while the buffer stores the sampling results in 16 bits, the
 * last 8 bit will always be 0. So we will only be storing the effective 8 bits
 * in a 2 digit hex format.
 */
std::string
PicoUnit::WaveformString( const int16_t channel, const unsigned capture ) const
{
  const unsigned length = presamples+postsamples;
  std::string    ans( 2 * length, '\0' );
  for( unsigned i = 0; i < length; ++i ){
    const int16_t raw  = GetBuffer( channel, capture, i ) / 256;
    const int8_t  dig1 = ( raw >> 4 ) & 0xf;
    const int8_t  dig2 = raw & 0xf;
    ans[2 * i  ] = dig1 <= 9 ? '0'+dig1 : 'a'+( dig1 % 10 );
    ans[2 * i+1] = dig2 <= 9 ? '0'+dig2 : 'a'+( dig2 % 10 );
  }
  return ans;
}


/**
 * @brief Summing the waveform over the entire sample range.
 */
float
PicoUnit::WaveformSum( const int16_t  channel,
                       const unsigned capture,
                       const unsigned _intstart,
                       const unsigned _intstop,
                       const unsigned _pedstart,
                       const unsigned _pedstop ) const
{
  const unsigned length   = presamples+postsamples;
  double         pedvalue = 0;

  // Getting the pedestal value if required
  if( _pedstart != _pedstop ){
    const unsigned pedstart = std::max( unsigned(0), _pedstart );
    const unsigned pedstop  = std::min( length, _pedstop );
    for( unsigned i = pedstart; i < pedstop; ++i ){
      pedvalue += GetBuffer( channel, capture, i ) / 256;
    }
    pedvalue *= adc2mv( channel, 256 ) / (double)( pedstop-pedstart );
  }
  float ans = 0;

  // Running the additional parsing.
  const unsigned intstart = std::max( unsigned(0), _intstart );
  const unsigned intstop  = std::min( length, _intstop );
  for( unsigned i = intstart; i < intstop; ++i ){
    ans += GetBuffer( channel, capture, i ) / 256;
  }
  ans *= adc2mv( channel, 256 );
  ans -= pedvalue * ( intstop-intstart );
  ans *= -2;

  // We will always be using 2ns time slices, inverting for positive number
  return ans;
}


/**
 * @brief Getting the maximum value of the value.
 */
int
PicoUnit::WaveformAbsMax( const int16_t channel ) const
{
  const unsigned length = presamples+postsamples;
  int            ans    = -256;
  for( unsigned cap = 0; cap < ncaptures; ++cap ){
    for( unsigned i = 0; i < length; ++i ){
      const int16_t raw = GetBuffer( channel, cap, i ) / 256;
      ans = std::max( ans, abs( raw ) );
    }
  }
  return ans;
}


/**
 * @brief Dumping the current picoscope configuration on the screen for
 * inspection.
 *
 * As this information is mainly for debugging via the text console, we will not
 * use the official logging interface
 */
void
PicoUnit::PrintInfo() const
{
  static const char description[5][25] = {
    "Driver Version", "USB Version", "Hardware Version", "Variant Info",
    "Serial" };
  int16_t           r = 0;
  char              inputline[80];
  int32_t           variant;
  std::string       output_table = "";

  for( unsigned i = 0; i < 5; i++ ){
    ps5000GetUnitInfo( device, (int8_t*)inputline, sizeof( inputline ), &r, i );
    if( i == 3 ){ variant = atoi( inputline ); }
    add_to_table( output_table, "%25s | %s\n", description[i], inputline );
  }

  add_to_table( output_table,
                "%25s | %d (%dns)\n",
                "Time interval",
                timebase,
                timeinterval );

  const auto minrange = variant == 5203 ? PS5000_100MV : variant ==
                        5204 ? PS5000_100MV : PS5000_MAX_RANGES;
  const auto maxrange = variant == 5203 ? PS5000_20V  : variant ==
                        5204 ? PS5000_20V  : PS5000_MAX_RANGES;

  // Printing voltage range information
  for( int i = minrange; i <= maxrange; ++i ){
    add_to_table( output_table,
                  "%25s | [%c] %2d (%5dmV) [Res: %.3fmV]\n",
                  ( i == minrange ? "Voltage Range index" : "" ),
                  ( i == range[0] ? 'A' : i == range[1] ? 'B' : ' ' ),
                  ( i ),
                  ( (int)inputRanges[i] ),
                  ( (float)inputRanges[i] / PS5000_MAX_VALUE * 256 ) );
  }

  // Channel information
  for( unsigned i = PS5000_CHANNEL_A; i <= PS5000_EXTERNAL; ++i ){
    add_to_table( output_table,
                  "%25s | %2d (%s) [%c]\n",
                  ( i == PS5000_CHANNEL_A ? "Channel index" : "" ),
                  i,
                  ( i == PS5000_EXTERNAL ? "External trigger" : "TEMP" ),
                  ( i == triggerchannel  ? 'T' : ' ' ) );
  }

  // Trigger direction
  for( unsigned i = RISING; i <= RISING_OR_FALLING; ++i ){
    add_to_table( output_table,
                  "%25s | %2d (%s) [%c]\n",
                  ( i == RISING ? "Trig. direction" : "" ),
                  ( i ),
                  ( i == RISING ? "RISING" : i == FALLING ? "FALLING" : i ==
                    RISING_OR_FALLING ? "RISING OR FALLING" : "" ),
                  ( i == triggerdirection ? 'V' : ' ' ) );
  }
  add_to_table( output_table,
                "%25s | %.2fmV (ADC:%d)\n",
                "Trigger Level",
                triggerlevel,
                int(triggerchannel ==
                    PS5000_EXTERNAL ? ( triggerlevel * PS5000_MAX_VALUE )
                    / 20000 : ( triggerlevel * PS5000_MAX_VALUE )
                    / inputRanges[range[triggerchannel]]) );
  add_to_table( output_table,
                "PRE:%10d | POST:%10d | NBLOCKS:%10d\n",
                presamples,
                postsamples,
                ncaptures );

  printdebug( DeviceName, output_table );
}


/**
 * @brief Making sure the time setting is correct.
 */
void
PicoUnit::FindTimeInterval()
{
  unsigned nsamples = 1000;// This in one u-sec!
  timebase = 0;
  while( ps5000GetTimebase( device,
                            timebase,
                            nsamples,
                            &timeinterval,
                            true,// allow oversampling
                            &maxsamples,
                            0// ????? Magic number
                            ) ){
    timebase++;
  }
}


PicoUnit::PicoUnit() : device ( 0 ),
  triggerchannel              ( PS5000_EXTERNAL ),
  triggerdirection            ( FALLING ),
  triggerlevel                ( 500 ),
  triggerdelay                ( 0 ),
  presamples                  ( 0 ),
  postsamples                 ( 0 ),
  ncaptures                   ( 0 )
{
  range[0] = 6;
  range[1] = 7;
}


PicoUnit::~PicoUnit()
{
  printinfo( DeviceName, "Closing the PICOSCOPE interface" );
  ps5000CloseUnit( device );
  printinfo( DeviceName, "PICOSCOPE interface closed" );
}


IMPLEMENT_SINGLETON( PicoUnit );
