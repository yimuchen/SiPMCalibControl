/*
   // https://elinux.org/RPi_GPIO_Code_Samples#Direct_register_access
   // Access from ARM Running Linux
 #include <fcntl.h>
 #include <stdio.h>
 #include <stdlib.h>
 #include <sys/mman.h>
 #include <unistd.h>

 #include <chrono>
 #include <thread>

 #define BCM2708_PERI_BASE 0x3F000000
 #define GPIO_BASE         ( BCM2708_PERI_BASE + 0x200000 )// GPIO controller
 #define PAGE_SIZE         ( 4*1024 )
 #define BLOCK_SIZE        ( 4*1024 )

   volatile unsigned* gpio;// I/O Access pointer
   int mem_fd;
   void* gpio_map;


   // GPIO setup macros.
   // Always use INP_GPIO(x) before using OUT_GPIO(x) or SET_GPIO_ALT(x,y)
 #define INP_GPIO( g ) *( gpio+( ( g )/10 ) ) &= ~( 7<<( ( ( g )%10 )*3 ) )
 #define OUT_GPIO( g ) *( gpio+( ( g )/10 ) ) |= ( 1<<( ( ( g )%10 )*3 ) )
 #define GPIO_SET *( gpio+7 )// sets   bits which are 1 ignores bits which are 0
 #define GPIO_CLR *( gpio+10 )// clears bits which are 1 ignores bits which are 0

   int
   main( int argc, char** argv )
   {
   // Immediate early exit if this is a personal laptop.
 #ifndef __arm__
   if( argc != 4 ){
    printf( "triggerpulse should not be used outside the raspberry pi!\n" );
    exit( -1 );
   }
   return 0;
 #endif

   if( argc != 4 ){
    printf( "triggerpulse <pin-number> <number-of-pulses> "
            "<microsecond between pulses>" );
    exit( -1 );
   }
   const unsigned pin  = std::stoi( argv[1] );
   const unsigned reps = std::stoi( argv[2] );
   const unsigned wait = std::stoi( argv[3] );

   // Setting up the I/O stuff
   // open /dev/mem
   if( ( mem_fd = open( "/dev/mem", O_RDWR|O_SYNC ) ) < 0 ){
    printf( "can't open /dev/mem \n" );
    exit( -1 );
   }

   // mmap GPIO
   gpio_map = mmap(
    NULL,// Any adddress in our space will do
    BLOCK_SIZE,// Map length
    PROT_READ|PROT_WRITE,// Enable reading & writting to mapped memory
    MAP_SHARED,// Shared with other processes
    mem_fd,// File to map
    GPIO_BASE// Offset to GPIO peripheral
    );

   close( mem_fd );// No need to keep mem_fd open after mmap

   if( gpio_map == MAP_FAILED ){
    printf( "mmap error %p\n", gpio_map );// errno also set!
    exit( -1 );
   }

   // Always use volatile pointer!
   gpio = (volatile unsigned*)gpio_map;

   INP_GPIO( pin );// must use INP_GPIO before we can use OUT_GPIO
   OUT_GPIO( pin );

   for( unsigned i = 0; i < reps; ++i ){
    GPIO_SET = 1<<pin;
    GPIO_CLR = 1<<pin;
    if( reps > 1 )
      std::this_thread::sleep_for( std::chrono::microseconds( wait ) );
   }

   return 0;

   }// main

 */


#include <stdio.h>
#include <stdlib.h>
#include <string>
#include <wiringPi.h>

int
main ( int argc, char* argv[] )
{
#ifndef __arm__
  if( argc != 4 ){
    printf( "triggerpulse should not be used outside the raspberry pi!\n" );
    exit( -1 );
  }
  return 0;
#endif

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
}
