#include "gcoder.cc"

#include <atomic>
#include <chrono>
#include <iostream>
#include <thread>

void MonitorThread( std::atomic<bool>& run_flag )
{
  unsigned counter = 0;

  while( run_flag ){
    std::cout << "Counter:" << counter  << std::endl;
    counter++;
    std::this_thread::sleep_for( std::chrono::milliseconds( 100 ) );
  }
}


int
main()
{
  GCoder gcoder;
  std::atomic<bool> runflag( true );
  std::thread mthread = std::thread( MonitorThread, std::ref( runflag ) );

  gcoder.InitPrinter( "/dev/ttyUSB0" );
  gcoder.MoveTo( 100, 100, 20 );
  std::this_thread::sleep_for( std::chrono::seconds( 1 ) );
  gcoder.MoveTo( 10, 10, 10  );
  std::this_thread::sleep_for( std::chrono::seconds( 1 ) );

  runflag = false;
  mthread.join();

  return 0;


}
