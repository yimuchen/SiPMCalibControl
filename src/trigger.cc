#include "trigger.hpp"

#include <fcntl.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>

#include <chrono>
#include <cstdio>
#include <stdexcept>
#include <thread>

void
Trigger::Init()
{
  static const int BCM2708_PERI_BASE = 0x3F000000;
  static const int GPIO_BASE         = ( BCM2708_PERI_BASE + 0x200000 );
  static const int PAGE_SIZE         = 4*1024;
  static const int BLOCK_SIZE        = 4*1024;
  int mem_fd;
  void* gpio_map;
  char errormessage[256];

  if( ( mem_fd = open( "/dev/mem", O_RDWR|O_SYNC ) ) < 0 ){
    throw std::runtime_error( "Can't open /dev/mem" );
  }

  /* mmap GPIO */
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
    sprintf( errormessage, "mmap error %d", MAP_FAILED );
    throw std::runtime_error( errormessage );// errno also set!
  }

  // Always use volatile pointer!
  gpio = (volatile unsigned*)gpio_map;
}

void
Trigger::Pulse( const unsigned n )
{
  static const int g = 21;
  input_gpio( g );// must use INP_GPIO before we can use OUT_GPIO
  out_gpio( g );

  for( unsigned i = 0; i < n; ++i ){
    gpio_set( g );
    gpio_clear( g );
    if( n > 1 ){
      std::this_thread::sleep_for( std::chrono::microseconds( 100 ) );
    }
  }
}

Trigger::Trigger()
{
  Init();
}

Trigger::~Trigger()
{}

/******************** BOOST PYTHON STUFF ********************** */
#include <boost/python.hpp>

BOOST_PYTHON_MODULE( trigger )
{
  boost::python::class_<Trigger>( "Trigger" )
  .def( "pulse", &Trigger::Pulse )
  .def( "init",  &Trigger::Init)
  ;
}
