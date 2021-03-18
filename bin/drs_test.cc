#include "drs.cc"

int main()
{
  DRSContainer drs;
  drs.Init();

  drs.SetTrigger(4, 0.05, 0, 550 );
  for( int i = 0 ; i< 10 ; ++i ){
    drs.StartCollect();
    drs.TimeSlice(1);
    drs.DumpBuffer(1);

  }
  return 0;
}