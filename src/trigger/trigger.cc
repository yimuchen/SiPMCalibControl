#include <trigger.hpp>

#include <stdlib.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>

#include <stdexcept>
#include <thread>
#include <boost/format.hpp>

void trigger::pulse()
{
  int g = 4;
  INP_GPIO(g); // must use INP_GPIO before we can use OUT_GPIO
  OUT_GPIO(g);

  for( unsigned long long i = 0 ; i < 1e8 ; ++i ){
    GPIO_SET(g);
    GPIO_CLR(g);
  }
}


void trigger::init()
{
  static const int BCM2708_PERI_BASE = 0x3F000000;
  static const int GPIO_BASE         = (BCM2708_PERI_BASE + 0x200000);
  static const int PAGE_SIZE (4*1024);
  static const int BLOCK_SIZE (4*1024);
  int  mem_fd;
  void *gpio_map;

  if( (mem_fd = open( "/dev/mem", O_RDWR|O_SYNC ) ) < 0 ){
    throw std::runtime_error("Can't open /dev/mem");
  }

  /* mmap GPIO */
  gpio_map = mmap(
    NULL,               // Any adddress in our space will do
    BLOCK_SIZE,         // Map length
    PROT_READ|PROT_WRITE,  // Enable reading & writting to mapped memory
    MAP_SHARED,         // Shared with other processes
    mem_fd,             // File to map
    GPIO_BASE           // Offset to GPIO peripheral
    );

  close( mem_fd );// No need to keep mem_fd open after mmap

  if( gpio_map == MAP_FAILED ){
    throw std::runtime_error( (boost::format("mmap error %d\n") % MAP_FAILED).str() );// errno also set!
  }

  // Always use volatile pointer!
  gpio = (volatile unsigned*)gpio_map;
}

trigger::trigger(){}
trigger::~trigger()
{}