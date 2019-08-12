   // https://elinux.org/RPi_GPIO_Code_Samples#Direct_register_access
   // Access from ARM Running Linux

// USING WIRINGPI INSTEAD for stability

#include <stdio.h>
#include <stdlib.h>
#include <string>
#ifdef __arm__
#include <wiringPi.h>
#else
#include <unistd.h>
#endif

int
main ( int argc, char* argv[] )
{
#ifndef __arm__
  if( argc != 4 ){
    printf( "triggerpulse should not be used outside the raspberry pi!\n" );
    exit( -1 );
  }
  return 0;
#else
  if( argc != 4 ){
    printf( "triggerpulse <pin-number> <number-of-pulses> "
      "<microsecond between pulses>\n" );
    exit( -1 );
  }
  const unsigned pin  = std::stoi( argv[1] );
  const unsigned reps = std::stoi( argv[2] );
  const unsigned wait = std::stoi( argv[3] );

  if( wiringPiSetup() == -1 ){
    return 1;
  }

  pinMode( pin, OUTPUT );

  for( unsigned i = 0; i < reps ; ++i ){
    digitalWrite( pin, 1 );// On
    delayMicroseconds( 1 );
    digitalWrite( pin, 0 );// Off
    delayMicroseconds( wait );
  }

  return 0;
#endif
}
