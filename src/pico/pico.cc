#include "pico.hpp"

#include <boost/format.hpp>
#include <iostream>
#include <stdexcept>


static const float inputRanges[PS5000_MAX_RANGES] = {
  10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000 };

PicoUnit::PicoUnit()
{
  auto status = ps5000OpenUnit( &device );

  if( status != PICO_OK ){
    throw std::runtime_error( ( boost::format(
      "Cannot open picotech device (Error code:%d)" )%status ).str() );
  }

  // Setting up default settings
  SetVoltageRange( PS5000_100MV );
  SetTrigger( 0, 0 );// 0 delay, indefinite trigger wait time.
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
PicoUnit::SetVoltageRange( PS5000_RANGE newrange )
{
  const static int16_t enable     = 1;
  const static int16_t dc_coupled = 1;

  auto status = ps5000SetChannel( device,
    PS5000_CHANNEL_A, enable,
    dc_coupled, newrange );

  if( status != PICO_OK ){
    throw std::runtime_error( ( boost::format(
      "Error setting up channel (Error code:%d)" )%status ).str() );
  }

  status = ps5000SetChannel( device,
    PS5000_CHANNEL_B, enable,
    dc_coupled, newrange );

  if( status != PICO_OK ){
    throw std::runtime_error( ( boost::format(
      "Error setting up channel (Error code:%d)" )%status ).str() );
  }

  range = newrange;
}

void
PicoUnit::SetTrigger( unsigned newdelay, int16_t newwait )
{
  static const int16_t enable = 1;
  // Always setting up such that it waits for a rising external trigger
  auto status = ps5000SetSimpleTrigger( device,
    enable,
    PS5000_CHANNEL_A,
    PS5000_MAX_VALUE / 4,// Random large number,
    // expecting rise edge to be sharp.
    RISING,
    newdelay,
    newwait );

  if( status != PICO_OK ){
    throw std::runtime_error( ( boost::format(
      "Error setting up trigger (Error code: %d)" )%status ).str() );
  }

  triggerdelay = newdelay;
  triggerwait  = newwait;
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
    throw std::runtime_error( "Error setting capture" );
  }

  if(  post + pre > maxsamples ){
    std::cout << "Warning! requested samples greater than maximum allowed samples, truncating to maximum" << std::endl;
    post = maxsamples - pre;
  }
  ncaptures = ncaps;
  presamples  = pre;
  postsamples = post;

  // Resizing the buffers
  bufferA.resize( ncaptures );
  bufferB.resize( ncaptures );
  overflowbuffer = std::unique_ptr<int16_t[]>( new int16_t[pre+post] );

  for( unsigned i = 0; i < ncaptures; ++i ){
    bufferA[i] = std::unique_ptr<int16_t[]>( new int16_t[pre+post] );
    bufferB[i] = std::unique_ptr<int16_t[]>( new int16_t[pre+post] );
  }
}

void
PicoUnit::StartRapidBlock()
{
  auto status = ps5000RunBlock( device,
    presamples, postsamples,
    timebase,// minimal temporal resolution
    true,// enable oversampling.. ???
    &runtime,// Saving runtime information
    0,// memory index to store information
    nullptr, nullptr// Using is ready, don't need to set here
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
  for( unsigned i = 0; i < presamples + postsamples; ++i  ){
    for( unsigned j = 0; j < ncaptures; ++j ){
      std::cout << boost::format( "(%8.2f,%8.2f)  " )
        % adc2mv( bufferA[j][i] )
        % adc2mv( bufferB[j][i] );
    }

    std::cout << std::endl;
  }
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

  std::cout << "timebase: " << timebase  << std::endl
            << "nsamples: "  << nsamples << std::endl
            << "maxsamples:" << maxsamples << std::endl
            << "timeinterval:" << timeinterval << std::endl;
}
