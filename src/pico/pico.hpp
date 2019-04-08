#ifndef PICO_HPP
#define PICO_HPP

#include <libps5000-1.5/ps5000Api.h>
#include <memory>
#include <string>
#include <vector>

class PicoUnit
{
public:
  PicoUnit();
  PicoUnit( const PicoUnit& ) = delete;
  PicoUnit( const PicoUnit&& ) = delete;

  ~PicoUnit();

  void SetVoltageRange( PS5000_RANGE );
  void SetTrigger( unsigned delay, int16_t maxwait );
  void SetBlockNums( unsigned ncaps, unsigned postsamples, unsigned presamples );
  void StartRapidBlock();
  void WaitTillReady();
  bool IsReady();
  void FlushToBuffer();

  // Conversion method.
  float adc2mv( int16_t adc ) const;

  // Debugging methods
  void DumpBuffer() const;

private:
  int16_t device;// integer representing device in driver API

  PS5000_RANGE range;
  unsigned triggerdelay;
  uint16_t triggerwait;

  unsigned timebase;// integer code to temporal spacing.
  int timeinterval;// temporal spacing in nano seconds.
  unsigned presamples;
  unsigned postsamples;// number of temporal samples for data collection.
  int maxsamples;// maximum number of time samples
  unsigned ncaptures;// Number of block capture for perform per function call
  int runtime;// storing runtime for Rapid block

  std::vector<std::unique_ptr<int16_t[]> > bufferA;
  std::vector<std::unique_ptr<int16_t[]> > bufferB;
  std::unique_ptr<int16_t[]> overflowbuffer;

  // Helper functions for sanity check
  void findTimeInterval();// Running once and not changing;
};

#endif
