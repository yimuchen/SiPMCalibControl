#include <libps5000-1.5/ps5000Api.h>

#include "logger.hpp"
#include "pico.hpp"

#include <boost/format.hpp>
#include <iostream>
#include <stdexcept>


static const float inputRanges[PS5000_MAX_RANGES] = {
  10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000 };

PicoUnit::PicoUnit()
{
}

void
PicoUnit::Init()
{
  if( device ){
    ps5000CloseUnit( device );
  }

  const auto status = ps5000OpenUnit( &device );

  if( status != PICO_OK ){
    throw std::runtime_error( ( boost::format(
      "Cannot open picotech device (Error code:%d)" )%status ).str() );
  }

  // Setting up default settings
  SetVoltageRange( PS5000_100MV );
  SetTrigger( PS5000_EXTERNAL, RISING, 2000, 0, 0 );// 0 delay, indefinite trigger wait time.
  findTimeInterval();
}

PicoUnit::~PicoUnit()
{
  ps5000CloseUnit( device );
}

float
PicoUnit::adc2mv( int16_t adc ) const
{ return adc * inputRanges[range] / PS5000_MAX_VALUE; }

void
PicoUnit::SetVoltageRange( const int newrange )
{
  const static int16_t enable     = 1;
  const static int16_t dc_coupled = 1;

  auto status = ps5000SetChannel( device,
    PS5000_CHANNEL_A, enable,
    dc_coupled, (PS5000_RANGE)newrange );

  if( status != PICO_OK ){
    throw std::runtime_error( ( boost::format(
      "Error setting up channel (Error code:%d)" )%status ).str() );
  }

  status = ps5000SetChannel( device,
    PS5000_CHANNEL_B, enable,
    dc_coupled, (PS5000_RANGE)newrange );

  if( status != PICO_OK ){
    throw std::runtime_error( ( boost::format(
      "Error setting up channel (Error code:%d)" )%status ).str() );
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

  // Always setting up such that it waits for a rising external trigger
  auto status = ps5000SetSimpleTrigger( device,
    enable,
    (PS5000_CHANNEL)channel,
    leveladc,
    (THRESHOLD_DIRECTION)direction,
    newdelay,// delay is in units of 10 timeintervals
    maxwait );

  if( status != PICO_OK ){
    throw std::runtime_error( ( boost::format(
      "Error setting up trigger (Error code: %d)" )%status ).str() );
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
  int maxcapture;

  auto status = ps5000MemorySegments( device,
    ncaps,// Number of captures per rapid block to store
    &maxcapture
    );

  status = ps5000SetNoOfCaptures( device, ncaps );
  if( status != PICO_OK ){
    throw std::runtime_error( ( boost::format(
      "Error setting rapid block capture (Code%d)" )%status ).str() );
  }

  if(  post + pre > maxsamples ){
    std::cout << "Warning! requested samples greater than maximum allowed samples, truncating to maximum" << std::endl;
    post = maxsamples - pre;
  }
  if( ncaptures != ncaps  || presamples + postsamples != pre + post ){
    ncaptures = ncaps;

    // Resizing the buffers
    bufferA.resize( ncaptures );
    bufferB.resize( ncaptures );
    overflowbuffer.reset( new int16_t[pre+post] );

    for( unsigned i = 0; i < ncaptures; ++i ){
      bufferA[i].reset( new int16_t[ pre+post ] );
      bufferB[i].reset( new int16_t[ pre+post ] );
    }
  }
  presamples  = pre;
  postsamples = post;
}

void
PicoUnit::StartRapidBlock()
{
  auto status = ps5000RunBlock( device,
    presamples, postsamples,
    timebase,// minimal temporal resolution
    true,// enable oversampling.. ???
    nullptr,// Not saving runtime information
    0,// memory index to store information
    nullptr, nullptr// Using IsReady, don't need to set here
    );

  if( status != PICO_OK ){
    throw std::runtime_error( ( boost::format(
      "Error setting up run block (Error code:%d" )%status ).str() );
  }

  for( unsigned block = 0; block < ncaptures; ++block ){
    status = ps5000SetDataBufferBulk( device,
      PS5000_CHANNEL_A,
      bufferA[block].get(),
      presamples + postsamples, block );
    status = ps5000SetDataBufferBulk( device,
      PS5000_CHANNEL_B,
      bufferB[block].get(),
      presamples + postsamples, block );

    if( status != PICO_OK ){
      throw std::runtime_error( ( boost::format(
        "Error setting up data buffer" )%status ).str() );
    }
  }
}

void
PicoUnit::WaitTillReady()
{
  while( !IsReady() ){
  }

  FlushToBuffer();
  return;
}

bool
PicoUnit::IsReady()
{
  int16_t ready;
  ps5000IsReady( device, &ready );
  return ready;
}

void
PicoUnit::FlushToBuffer()
{
  uint32_t actualsamples = presamples + postsamples;
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
  static const unsigned maxcols = 6;
  const unsigned ncols          = ncaptures < maxcols ? ncaptures : maxcols;
  std::string line;

  // Header line
  line = ( boost::format( "%-7s | " ) % "Time" ).str();

  for( unsigned j = 0; j < ncols; ++j ){
    line += ( boost::format( "Capture:%-11d |" ) % j ).str();
  }

  printmsg( GREEN( "[PICOBUFFER]" ), line );

  for( unsigned i = 0; i < presamples + postsamples; ++i  ){
    const int t = (int)i - (int)presamples;
    line = ( boost::format( "%5dns | " )% ( t*timeinterval ) ).str();

    for( unsigned j = 0; j < ncols; ++j ){
      line += ( boost::format( "(%8.2f,%8.2f) |" )
                % adc2mv( bufferA[j][i] )
                % adc2mv( bufferB[j][i] ) ).str();
    }

    printmsg( GREEN( "[PICOBUFFER]" ), line );
  }
}


int16_t
PicoUnit::GetBuffer(
  const int      channel,
  const unsigned cap,
  const unsigned sample ) const
{
  return channel == 0 ? bufferA[cap][sample]  : bufferB[cap][sample];
}

void
PicoUnit::PrintInfo() const
{
  static const std::string description[5] =
  { "Driver Version", "USB Version", "Hardware Version",
    "Variant Info",   "Serial"    };
  int16_t r = 0;
  char line[80];
  int32_t variant;

  for( unsigned i = 0; i < 5; i++ ){
    ps5000GetUnitInfo( device, (int8_t*)line, sizeof( line ), &r, i );
    if( i == 3 ){
      variant = atoi( line );
    }
    printmsg( GREEN( "[PICO]" ),
      ( boost::format( "%25s | %s" )%description[i] % line ).str() );
  }

  printmsg( GREEN( "[PICO]" ),
    ( boost::format( "%25s | %d (%dns)" )
      % "Time interval"
      % timebase
      % timeinterval ).str() );

  const auto minrange = variant == 5203 ? PS5000_100MV :
                        variant == 5204 ? PS5000_100MV :
                        PS5000_MAX_RANGES;
  const auto maxrange = variant == 5203 ? PS5000_20V  :
                        variant == 5204 ? PS5000_20V :
                        PS5000_MAX_RANGES;

  // Printing voltage range information
  for( unsigned i = minrange; i <= maxrange; ++i ){
    printmsg( GREEN( "[PICO]" ),
      ( boost::format( "%25s | [%c] %2d (%5dmV) [Res: %.3fmV]" )
        % ( i == minrange ? "Voltage Range index" : "" )
        % ( i == range ?  'V' : ' ' )
        % i
        % inputRanges[i]
        % ((float)inputRanges[i] / PS5000_MAX_VALUE * 256)
      ).str() );
  }

  // Channel information
  for( unsigned i = PS5000_CHANNEL_A; i <= PS5000_EXTERNAL; ++i ){
    printmsg( GREEN( "[PICO]" ),
      ( boost::format( "%25s | %2d (%s) [%c]" )
        % ( i == PS5000_CHANNEL_A ? "Channel index" : "" )
        % i
        % ( i == PS5000_EXTERNAL ? "External trigger" :
            std::string( 1, 'A' + i ) )
        % ( i == triggerchannel  ? 'T' : ' ' ) ).str() );
  }

  for( unsigned i = RISING; i <= RISING_OR_FALLING; ++i ){
    printmsg( GREEN( "[PICO]" ),
      ( boost::format( "%25s | %2d (%s) [%c]" )
        % ( i == RISING ? "Trig. direction" : "" )
        % i
        % ( i == RISING ? "RISING" :
            i == FALLING ? "FALLING" :
            i == RISING_OR_FALLING ? "RISING OR FALLING" :
            "" )
        % ( i == triggerdirection ? 'V' : ' ' )
      ).str() );
  }

  printmsg( GREEN( "[PICO]" ),
    ( boost::format( "%25s | %.2fmV (ADC:%d)" )
      % "Trigger Level"
      % triggerlevel
      % int( triggerchannel == PS5000_EXTERNAL ?
        ( triggerlevel * PS5000_MAX_VALUE ) / 20000 :
        ( triggerlevel * PS5000_MAX_VALUE ) / inputRanges[range] )
    ).str() );
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
