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


  gpio.Pulse( 100, 10 );

  /*
     for( int i = 0; i < 100; ++i ){
     gpio.SetPWM( 0, 1.0, 1e4 );
     usleep( 1e4 );
     gpio.SetPWM( 0, 0.0, 1e4 );
     usleep( 1e4 );
     }
   */

  for( int i = 0; i < 10000; ++i ){
    std::cout << "\r"
              << gpio.ReadNTCTemp( 0 ) << "|"
              << gpio.ReadADC( 0 ) << " [[]] "
              << gpio.ReadRTDTemp( 1 ) << "|"
              << gpio.ReadADC(1) << std::flush;
    usleep( 1e5 );
  }


  std::cout << std::endl;

  return 0;
}
