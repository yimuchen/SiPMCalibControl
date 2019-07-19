#include "trigger.hpp"
#include <chrono>
#include <thread>
int main()
{
  Trigger t;
  t.Init();

  while(1){
    t.Pulse(1);
    std::this_thread::sleep_for( std::chrono::microseconds(1) );
  }
}