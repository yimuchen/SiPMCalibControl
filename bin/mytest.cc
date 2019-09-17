#ifdef __arm__
#include <libps5000/ps5000Api.h>
#else
#include <libps5000-1.5/ps5000Api.h>
#endif

#include "pico.hpp"
#include <iostream>

int
main( int argc, char* argv[] )
{
  PicoUnit pico;
  pico.Init();
  pico.SetBlockNums( 500, 120, 0 );
  pico.SetVoltageRange( PS5000_100MV );
  ///
  pico.SetTrigger( PS5000_EXTERNAL, RISING, 200, 8, 1 );

 for( int i = 0; i <  20 ; ++i  ){
   std::cout << i << std::endl;
   pico.StartRapidBlock();
   pico.WaitTillReady();
   // pico.DumpBuffer();
 }

 for( int i = 0; i <  20 ; ++i  ){
   std::cout << i << std::endl;
   pico.StartRapidBlock();
   pico.WaitTillReady();
   // pico.DumpBuffer();
 }

  return 0;
}
