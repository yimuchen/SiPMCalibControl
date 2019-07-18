#include <iostream>
#include "pico.hpp"
#include <libps5000/ps5000Api.h>

int
main( int argc, char* argv[] )
{
  PicoUnit pico;
  pico.Init();
  pico.SetBlockNums( 3, 1000, 10 );
  pico.SetVoltageRange( PS5000_5V );
  ///
  pico.SetTrigger( PS5000_EXTERNAL, RISING, 2000, 0, 0 );
  pico.StartRapidBlock();
  pico.WaitTillReady();
  pico.FlushToBuffer();
  pico.DumpBuffer();

  // std::cout << "\n\n\n" << std::endl;
  // pico.SetTrigger( 100, 0 );
  // pico.StartRapidBlock();
  // pico.WaitTillReady();
  // pico.DumpBuffer();


  return 0;


  /*
  static const short enable    = 1;
  static const short disable   = 0;
  static const short dccoupled = 1;
  short device;

  auto status = ps5000OpenUnit( &device );
  if( status != PICO_OK ){
    std::cout << "Error opening device" << std::endl;
    return 0;
  }

  status = ps5000SetChannel( device,
    PS5000_CHANNEL_A, enable,
    dccoupled, PS5000_100MV );
  status = ps5000SetChannel( device,
    PS5000_CHANNEL_B, enable,
    dccoupled, PS5000_100MV );

  if( status != PICO_OK ){
    std::cout << "Error setting up channels" << std::endl;
    return 0;
  }

  status = ps5000SetSimpleTrigger( device,
    enable,
    PS5000_EXTERNAL,
    1024,
    RISING,
    0,// No delay,
    10// 10 ms maximum waiting time
    );

  if( status != PICO_OK ){
    std::cout << "Error setting up trigger" << std::endl;
    return 0;
  }


  // Setting number of captures
  unsigned captures = 1024;// Number of trigger to collect for one block run
  unsigned samples  = 1000;// Number of samples to collect for each trigger
  int maxcapture;
  int runtime = 0;

  status = ps5000MemorySegments( device,
    captures,// Number of captures per rapid block to store
    &maxcapture
    );
  status = ps5000SetNoOfCaptures( device, captures );
  if( status != PICO_OK ){
    std::cout << "Error setting capture" << std::endl;
    return 0;
  }

  int timebase     = 1;
  int timeinterval = 0;
  int maxsamples   = 0;

  // Finding minimal temporal resolution
  while( ps5000GetTimebase( device, timebase, samples,
    &timeinterval, true, &maxsamples, 0 ) ){
    timebase++;
  }

  printf( "timebase: %hd\toversample:%hd\n", timebase, true );
  printf( "Time interval: %d", timeinterval );


  // Settin up to run rapid block
  status = ps5000RunBlock( device,
    0, samples,// No samples before trigger
    timebase,// minimal temporal resolution
    true,// enable oversampling.. ???
    &runtime,// Saving runtime information
    0,// memory index to store information
    nullptr, nullptr// Using is ready, don't need to set here
    );

  if( status != PICO_OK ){
    std::cout << "Error setting up run block" << std::endl;
    std::cout << "Status code: " << status << std::endl;
    return 0;
  }

  // Setting up memory buffer to store readout information
  int16_t channel_A_buffer[captures][samples];
  int16_t channel_B_buffer[captures][samples];
  int16_t overflow[captures];

  for( unsigned block = 0; block < captures; ++block ){
    status = ps5000SetDataBufferBulk( device,
      PS5000_CHANNEL_A,
      channel_A_buffer[block],
      samples, block );
    status = ps5000SetDataBufferBulk( device,
      PS5000_CHANNEL_B,
      channel_B_buffer[block],
      samples, block );

    if( status != PICO_OK ){
      std::cout << "Error setting up data buffer" << std::endl;
    }
  }

  // Waiting for block to finish
  int16_t ready = 0;

  std::cout << "Waiting for device to finish..." << std::endl;

  while( !ready ){
    ps5000IsReady( device, &ready );
  }

  uint32_t actualsamples = samples;
  ps5000GetValuesBulk( device,
    &actualsamples,
    0, captures-1,// flush range
    overflow// overflow buffer
    );


  std::cout << "Closing device" << std::endl;
  ps5000CloseUnit( device );
  */


  return 0;
}
