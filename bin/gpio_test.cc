#include <iostream>
#include "gpio.cc"

int
main( int argc, char** argv )
{

  GPIO gpio;
  gpio.Init();

  gpio.LightsOn();
  usleep(1e6);
  gpio.LightsOff();


  gpio.Pulse(100, 10);

  /*
  usleep(1e6);
  gpio.SetPWM( 0, 0.5, 1e5 );
  sleep(15);
  gpio.SetPWM( 0, 0.8, 1e5 );
  sleep(15);
  gpio.SetPWM( 0, 0.2, 1e5 );
  sleep(15);
  */


  for( int i = 0 ; i < 10 ; ++i ){
    std::cout << "\r" << gpio.ReadADC(0) << std::flush;
    usleep(1e3);
  } std::cout << std::endl;
  for( int i = 0 ; i < 10 ; ++i ){
    std::cout << "\r" << gpio.ReadADC(1) << std::flush;
    usleep(1e4);
  } std::cout << std::endl;
  for( int i = 0 ; i < 10 ; ++i ){
    std::cout << "\r" << gpio.ReadADC(2) << std::flush;
    usleep(1e4);
  } std::cout << std::endl;
  for( int i = 0 ; i < 10 ; ++i ){
    std::cout << "\r" << gpio.ReadADC(3) << std::flush;
    usleep(1e4);
  } std::cout << std::endl;

  return 0;
}
