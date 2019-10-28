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

  return 0;
}
