#include "gpio.cc"
#include <iostream>

int
main( int argc, char** argv )
{

  GPIO gpio;
  gpio.Init();

  gpio.LightsOn();
  usleep( 1e6 );
  gpio.LightsOff();

  gpio.SetPWM( 0, 0.9, 3e5 );
  // gpio.Pulse( 10000, 10000 );


  gpio.SetPWM( 0, 0.8, 1e5 );
  gpio.SetPWM( 1, 0.8, 1e5 );
  /*
     for( int i = 0; i < 100; ++i ){
     gpio.SetPWM( 0, 1.0, 1e4 );
     usleep( 1e4 );
     gpio.SetPWM( 0, 0.0, 1e4 );
     usleep( 1e4 );
     }
   */

  for( int i = 0; i < 10; ++i ){
    std::cout << "\r"
              << gpio.ReadNTCTemp( 0 ) << "|"
              << gpio.ReadADC( 0 ) << "\t ***  \t"
              << gpio.ReadRTDTemp( 1 ) << "|"
              << gpio.ReadADC( 1 ) << "\t  ***  \t"
              << gpio.ReadADC( 2 ) << "\t  ***  \t"
              << gpio.ReadADC( 3 ) << "\r" << std::flush;
    usleep( 1e6 );
  }


  std::cout << std::endl;

  return 0;
}
