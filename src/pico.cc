#include <libps5000/ps5000Api.h>

#include "logger.hpp"

#include <chrono>
#include <cstdio>
#include <cstring>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

class PicoUnit
{
public:
  PicoUnit();

  ~PicoUnit();

  // Cannot specify serial device?
  void Init();

  int  VoltageRangeMax() const;
  int  VoltageRangeMin() const;
  void SetVoltageRange( int newrange );

  void SetTrigger(
    const int16_t  channel,
    const int16_t  direction,
    const float    level,
    const unsigned delay,
    const int16_t  maxwait );
  void SetBlockNums(
    const unsigned ncaps,
    const unsigned postsamples,
    const unsigned presamples );
  void StartRapidBlock();
  void WaitTillReady();
  bool IsReady();
  void FlushToBuffer();

  int16_t GetBuffer(
    const int      channel,
    const unsigned cap,
    const unsigned sample ) const;

  // Conversion method.
  float adc2mv( int16_t adc ) const;

  // Debugging methods
  void DumpBuffer() const;
  void PrintInfo() const;

  std::string WaveformString( const int16_t  channel,
                              const unsigned capture ) const;
  int WaveformSum( const int16_t  channel,
                   const unsigned capture ) const;

  int WaveformAbsMax( const int16_t channel ) const;

public:
  int16_t device;// integer representing device in driver API

  int range;
  uint16_t triggerchannel;
  uint16_t triggerdirection;
  float triggerlevel;
  unsigned triggerdelay;
  uint16_t triggerwait;

  unsigned timebase;// integer code to temporal spacing.
  int timeinterval;// temporal spacing in nano seconds.
  unsigned presamples;
  unsigned postsamples;// number of temporal samples for data collection.
  int maxsamples;// maximum number of time samples
  unsigned ncaptures;// Number of block capture for perform per function call
  int runtime;// storing runtime for Rapid block

private:
  std::vector<std::unique_ptr<int16_t[]> > bufferA;
  std::vector<std::unique_ptr<int16_t[]> > bufferB;
  std::unique_ptr<int16_t[]> overflowbuffer;

  // Helper functions for sanity check
  void findTimeInterval();// Running once and not changing;
};


static const float inputRanges[PS5000_MAX_RANGES] = {
  10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000 };

PicoUnit::PicoUnit() :
  device( 0 ),
  presamples( 0 ),
  postsamples( 0 ),
  ncaptures( 0 )
{}

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
      "Cannot open picotech device (Error code: %d)", status  );
    throw std::runtime_error( errormessage );
  }

  // Setting up default settings
  SetVoltageRange( PS5000_100MV );
  SetTrigger( PS5000_EXTERNAL, RISING, 2000, 0, 0 );
  // 0 delay, indefinite trigger wait time.
  SetBlockNums( 500, 0, 100 );
  findTimeInterval();
}

PicoUnit::~PicoUnit()
{
  ps5000CloseUnit( device );
}

float
PicoUnit::adc2mv( int16_t adc ) const
{ return adc * inputRanges[range] / PS5000_MAX_VALUE; }

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
PicoUnit::SetVoltageRange( const int newrange )
{
  const static int16_t enable     = 1;
  const static int16_t dc_coupled = 1;
  char errormessage[1024];

  auto status = ps5000SetChannel( device,
    PS5000_CHANNEL_A, enable,
    dc_coupled, (PS5000_RANGE)newrange );

  if( status != PICO_OK ){
    sprintf( errormessage,
      "Error setting up channel (Error code:%d)", status  );
    throw std::runtime_error( errormessage );
  }

  status = ps5000SetChannel( device,
    PS5000_CHANNEL_B, enable,
    dc_coupled, (PS5000_RANGE)newrange );

  if( status != PICO_OK ){
    sprintf( errormessage,
      "Error setting up channel (Error code:%d)", status  );
    throw std::runtime_error( errormessage );
  }

  range = newrange;
}

void
PicoUnit::SetTrigger(
  const int16_t  channel,
  const int16_t  direction,
  const float    level,
  const unsigned newdelay,
  const int16_t  maxwait )
{
  static const int16_t enable = 1;

  const int16_t leveladc
    = channel == PS5000_EXTERNAL ? ( level * PS5000_MAX_VALUE ) / 20000 :
      ( level * PS5000_MAX_VALUE ) / inputRanges[range];
  char errormessage[1024];

  // Always setting up such that it waits for a rising external trigger
  auto status = ps5000SetSimpleTrigger( device,
    enable,
    (PS5000_CHANNEL)channel,
    leveladc,
    (THRESHOLD_DIRECTION)direction,
    newdelay,// delay is in units of 10 timeintervals
    maxwait );

  if( status != PICO_OK ){
    sprintf( errormessage,
      "Error setting up trigger (Error code:%d)", status  );
    throw std::runtime_error( errormessage );
  }

  // Storing information
  triggerchannel   = channel;
  triggerdirection = direction;
  triggerlevel     = level;
  triggerdelay     = newdelay;
  triggerwait      = maxwait;
}

void
PicoUnit::SetBlockNums(
  unsigned ncaps, unsigned post, unsigned pre )
{
  char errormessage[1024];
  int maxcapture;

  auto status = ps5000MemorySegments( device,
    ncaps,// Number of captures per rapid block to store
    &maxcapture
    );

  status = ps5000SetNoOfCaptures( device, ncaps );
  if( status != PICO_OK ){
    sprintf( errormessage,
      "Error setting rapid block capture (Error code%d)", status );
    throw std::runtime_error( errormessage );
  }

  if(  post + pre > (unsigned)maxsamples ){
    sprintf( errormessage,
      "requested samples [%u+%u]greater than maximum allowed samples[%d],"
      "truncating to maximum",
      pre, post, maxsamples );
    printwarn( errormessage );
    post = maxsamples - pre;
  }

  // Resizing capture buffer only if needed (reqesting more stuff)
  if( ncaptures < ncaps ){
    bufferA.resize( ncaps );
    bufferB.resize( ncaps );

    for( unsigned i = ncaptures; i < ncaps; ++i ){
      bufferA[i].reset( new int16_t[presamples + postsamples] );
      bufferB[i].reset( new int16_t[presamples + postsamples] );
      if( bufferA[i] == nullptr || bufferB[i] == nullptr ){
        sprintf( errormessage,
          "Failed to initialize block memory buffer (%d/%d). Maybe try smaller "
          "number of captures"
               , i, ncaptures );
        throw std::runtime_error( errormessage );
      }
    }

    overflowbuffer.reset( new int16_t[ncaps] );
  }
  ncaptures = ncaps;

  if( presamples + postsamples < pre + post ){
    for( unsigned i = 0; i < ncaptures; ++i ){
      bufferA[i].reset( new int16_t[ pre+post ] );
      bufferB[i].reset( new int16_t[ pre+post ] );
      if( bufferA[i] == nullptr || bufferB[i] == nullptr ){
        sprintf( errormessage,
          "Failed to initialize block memory buffer (%d/%d). "
          "Maybe try smaller number of captures"
               , i, ncaptures );
        throw std::runtime_error( errormessage );
      }
    }
  }
  presamples  = pre;
  postsamples = post;
}

void
PicoUnit::StartRapidBlock()
{
  char errormessage[1024];
  auto status = ps5000RunBlock( device,
    presamples, postsamples,
    timebase,// minimal temporal resolution
    true,// enable oversampling.. ???
    nullptr,// Not saving runtime information
    0,// memory index to store information
    nullptr, nullptr// Using IsReady, don't need to set here
    );

  if( status != PICO_OK ){
    sprintf( errormessage,
      "Error setting up run block (Error code:%d", status );
    throw std::runtime_error( errormessage );
  }

}

void
PicoUnit::WaitTillReady()
{
  while( !IsReady() ){
    std::this_thread::sleep_for( std::chrono::microseconds( 5 ) );
  }

  return;
}

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

void
PicoUnit::FlushToBuffer()
{
  uint32_t actualsamples = presamples + postsamples;
  int status             = 0;
  char errormessage[1024];

  for( unsigned block = 0; block < ncaptures; ++block ){
    status = ps5000SetDataBufferBulk( device,
      PS5000_CHANNEL_A,
      bufferA[block].get(),
      actualsamples, block );
    status = ps5000SetDataBufferBulk( device,
      PS5000_CHANNEL_B,
      bufferB[block].get(),
      actualsamples, block );

    if( status != PICO_OK ){
      sprintf( errormessage,
        "Error setting up data buffer (Error code:%d)", status );
      throw std::runtime_error( errormessage );
    }
  }

  ps5000GetValuesBulk( device,
    &actualsamples,
    0, ncaptures-1,// flush range
    overflowbuffer.get()// overflow buffer
    );

}

// Debugging methods
void
PicoUnit::DumpBuffer() const
{
  static const std::string head = GREEN( "[PICOBUFFER]" );
  static const unsigned maxcols = 6;
  const unsigned ncols          = std::min( ncaptures,  maxcols );
  char line[1024];
  char tempstr[1024];

  // Header line
  sprintf( line, "%-7s | ", "Time" );

  for( unsigned j = 0; j < ncols; ++j ){
    sprintf( tempstr, "Capture:%-11d |", j );
    strcat( line, tempstr );
  }

  printmsg( head, line );

  for( unsigned i = 0; i < presamples + postsamples; ++i  ){
    const int t = (int)i - (int)presamples;
    sprintf( line, "%5dns | ", ( t*timeinterval ) );

    for( unsigned j = 0; j < ncols; ++j ){
      sprintf( tempstr, "(%8.2f,%8.2f) |",
        adc2mv( GetBuffer( 0, j, i ) ),
        adc2mv( GetBuffer( 1, j, i ) ) );
      strcat( line, tempstr );
    }

    printmsg( head, line );
  }

  // Two empty lines for aesthetic reasons
  printmsg( "" );
  printmsg( "" );
}

int16_t
PicoUnit::GetBuffer(
  const int      channel,
  const unsigned cap,
  const unsigned sample ) const
{
  return channel == 0 ? bufferA[cap][sample] : bufferB[cap][sample];
}

std::string
PicoUnit::WaveformString(
  const int16_t  channel,
  const unsigned capture
  ) const
{
  const unsigned length = presamples + postsamples;
  std::string ans( 2*length, '\0' );

  for( unsigned i = 0; i < length; ++i ){
    const int16_t raw = GetBuffer( channel, capture, i ) / 256;
    const int8_t dig1 = ( raw >> 4 ) & 0xf;
    const int8_t dig2 = raw & 0xf;
    ans[2*i  ] = dig1 <= 9 ? '0' + dig1 : 'a' + ( dig1 % 10 );
    ans[2*i+1] = dig2 <= 9 ? '0' + dig2 : 'a' + ( dig2 % 10 );
  }

  return ans;
}

int
PicoUnit::WaveformSum(
  const int16_t  channel,
  const unsigned capture
  ) const
{
  const unsigned length = presamples + postsamples;
  int ans               = 0;

  for( unsigned i = 0; i < length; ++i ){
    ans += GetBuffer( channel, capture, i ) / 256;
  }

  return ans * adc2mv( 256 );
}

int
PicoUnit::WaveformAbsMax( const int16_t channel ) const
{
  const unsigned length = presamples + postsamples;

  int ans = -256;

  for( unsigned cap = 0; cap < ncaptures; ++cap ){
    for( unsigned i = 0; i < length; ++i ){
      const int16_t raw = GetBuffer( channel, cap, i ) / 256;
      ans = std::max( ans, abs( raw ) );
    }
  }

  return ans;
}


void
PicoUnit::PrintInfo() const
{
  static const char description[5][25] = {
    "Driver Version",
    "USB Version",
    "Hardware Version",
    "Variant Info",
    "Serial"    };
  static const std::string picoinfo = GREEN( "[PICOINFO]" );

  int16_t r = 0;
  char inputline[80];
  char line[1024];
  int32_t variant;

  for( unsigned i = 0; i < 5; i++ ){
    ps5000GetUnitInfo( device, (int8_t*)inputline, sizeof( inputline ), &r, i );
    if( i == 3 ){ variant = atoi( inputline ); }
    sprintf( line, "%25s | %s", description[i], inputline );
    printmsg( picoinfo, line );
  }

  sprintf( line, "%25s | %d (%dns)", "Time interval", timebase, timeinterval );
  printmsg( picoinfo, line );

  const auto minrange = variant == 5203 ? PS5000_100MV :
                        variant == 5204 ? PS5000_100MV :
                        PS5000_MAX_RANGES;
  const auto maxrange = variant == 5203 ? PS5000_20V  :
                        variant == 5204 ? PS5000_20V :
                        PS5000_MAX_RANGES;

  // Printing voltage range information
  for( int i = minrange; i <= maxrange; ++i ){
    sprintf( line, "%25s | [%c] %2d (%5dmV) [Res: %.3fmV]",
      ( i == minrange ? "Voltage Range index" : "" ),
      ( i == range ?  'V' : ' ' ),
      ( i ),
      ( (int)inputRanges[i] ),
      ( (float)inputRanges[i] / PS5000_MAX_VALUE * 256 ) );
    printmsg( picoinfo, line );
  }

  // Channel information
  for( unsigned i = PS5000_CHANNEL_A; i <= PS5000_EXTERNAL; ++i ){
    sprintf( line, "%25s | %2d (%s) [%c]",
      ( i == PS5000_CHANNEL_A ? "Channel index" : "" ),
      i,
      ( i == PS5000_EXTERNAL ? "External trigger" : "TEMP" ),
      ( i == triggerchannel  ? 'T' : ' ' ) );
    printmsg( picoinfo, line );
  }

  // Trigger direction
  for( unsigned i = RISING; i <= RISING_OR_FALLING; ++i ){
    sprintf( line, "%25s | %2d (%s) [%c]",
      ( i == RISING ? "Trig. direction" : "" ),
      ( i ),
      ( i == RISING ? "RISING" :
        i == FALLING ? "FALLING" :
        i == RISING_OR_FALLING ? "RISING OR FALLING" :
        "" ),
      ( i == triggerdirection ? 'V' : ' ' ) );
    printmsg( picoinfo, line );
  }

  sprintf( line, "%25s | %.2fmV (ADC:%d)",
    "Trigger Level",
    triggerlevel,
    int(triggerchannel == PS5000_EXTERNAL ?
        ( triggerlevel * PS5000_MAX_VALUE ) / 20000 :
        ( triggerlevel * PS5000_MAX_VALUE ) / inputRanges[range]) );
  // Trigger level
  printmsg( picoinfo, line );
}

void
PicoUnit::findTimeInterval()
{
  unsigned nsamples = 1000;// This in one u-sec!
  timebase = 0;

  while( ps5000GetTimebase( device,
    timebase, nsamples, &timeinterval,
    true,// allow oversampling
    &maxsamples,
    0// ????? Magic number
    ) ){
    timebase++;
  }
}

/** BOOST PYTHON STUFF */
#ifndef STANDALONE
#include <boost/python.hpp>

BOOST_PYTHON_MODULE( pico )
{
  boost::python::class_<PicoUnit, boost::noncopyable>( "PicoUnit" )
  .def( "init",             &PicoUnit::Init            )
  .def( "settrigger",       &PicoUnit::SetTrigger      )
  .def( "rangemin",         &PicoUnit::VoltageRangeMin )
  .def( "rangemax",         &PicoUnit::VoltageRangeMax )
  .def( "setrange",         &PicoUnit::SetVoltageRange )
  .def( "setblocknums",     &PicoUnit::SetBlockNums    )
  .def( "startrapidblocks", &PicoUnit::StartRapidBlock )
  .def( "isready",          &PicoUnit::IsReady         )
  .def( "waitready",        &PicoUnit::WaitTillReady   )
  .def( "buffer",           &PicoUnit::GetBuffer       )
  .def( "flushbuffer",      &PicoUnit::FlushToBuffer   )
  .def( "dumpbuffer",       &PicoUnit::DumpBuffer      )
  .def( "printinfo",        &PicoUnit::PrintInfo       )
  .def( "adc2mv",           &PicoUnit::adc2mv          )
  .def( "waveformstr",      &PicoUnit::WaveformString  )
  .def( "waveformsum",      &PicoUnit::WaveformSum     )
  .def( "waveformmax",      &PicoUnit::WaveformAbsMax  )

  // Defining data members as readonly:
  .def_readonly( "device",           &PicoUnit::device           )
  .def_readonly( "range",            &PicoUnit::range            )
  .def_readonly( "presamples",       &PicoUnit::presamples       )
  .def_readonly( "postsamples",      &PicoUnit::postsamples      )
  .def_readonly( "ncaptures",        &PicoUnit::ncaptures        )
  .def_readonly( "timeinterval",     &PicoUnit::timeinterval     )
  .def_readonly( "triggerchannel",   &PicoUnit::triggerchannel   )
  .def_readonly( "triggerdirection", &PicoUnit::triggerdirection )
  .def_readonly( "triggerlevel",     &PicoUnit::triggerlevel     )
  .def_readonly( "triggerdelay",     &PicoUnit::triggerdelay     )
  .def_readonly( "triggerwait",      &PicoUnit::triggerwait      )
  ;
}
#endif
