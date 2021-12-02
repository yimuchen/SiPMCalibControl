#ifndef PICO_HPP
#define PICO_HPP

#include "singleton.hpp"
#include <memory>
#include <vector>

class PicoUnit
{
public:
  // Cannot specify serial device?
  void Init();

  int  VoltageRangeMax() const;
  int  VoltageRangeMin() const;
  void SetVoltageRange( const int16_t channel, const int newrange );

  void SetTrigger(
    const int16_t  channel,
    const int16_t  direction,
    const float    level,
    const unsigned delay,
    const int16_t  maxwait );
  void SetBlockNums(
    const unsigned ncaps,
    const unsigned postsamples,
    const unsigned presamples );
  void StartRapidBlock();
  void WaitTillReady();
  bool IsReady();
  void FlushToBuffer();

  int16_t GetBuffer(
    const int      channel,
    const unsigned cap,
    const unsigned sample ) const;

  // Conversion method.
  float adc2mv( const int16_t channel, const int16_t adc ) const;

  // Debugging methods
  void DumpBuffer() const;
  void PrintInfo() const;

  std::string WaveformString( const int16_t  channel,
                              const unsigned capture
                              ) const;
  float WaveformSum( const int16_t  channel,
                     const unsigned capture,
                     const unsigned intstart = -1,
                     const unsigned intstop  = -1,
                     const unsigned pedstart = -1,
                     const unsigned pedstop  = -1
                     ) const;

  int WaveformAbsMax( const int16_t channel ) const;

public:
  int16_t device;// integer representing device in driver API

  int range[2];
  uint16_t triggerchannel;
  uint16_t triggerdirection;
  float triggerlevel;
  unsigned triggerdelay;
  uint16_t triggerwait;

  unsigned timebase;// integer code to temporal spacing.
  int timeinterval;// temporal spacing in nano seconds.
  unsigned presamples;
  unsigned postsamples;// number of temporal samples for data collection.
  int maxsamples;// maximum number of time samples
  unsigned ncaptures;// Number of block capture for perform per function call
  int runtime;// storing runtime for Rapid block

  inline int
  rangeA() const { return range[0]; }
  inline int
  rangeB() const { return range[1]; }

private:
  std::vector<std::unique_ptr<int16_t[]> > bufferA;
  std::vector<std::unique_ptr<int16_t[]> > bufferB;
  std::unique_ptr<int16_t[]> overflowbuffer;

  // Helper functions for sanity check
  void FindTimeInterval();// Running once and not changing;

// Singleton stuff
  DECLARE_SINGLETON( PicoUnit );
};

#endif
