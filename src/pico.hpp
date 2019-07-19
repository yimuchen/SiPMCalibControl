#ifndef PICO_HPP
#define PICO_HPP

#include <memory>
#include <string>
#include <vector>

class PicoUnit
{
public:
  PicoUnit();

  ~PicoUnit();

  // Cannot specify serial device?
  void Init();

  void SetVoltageRange( int newrange );
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
  float adc2mv( int16_t adc ) const;

  // Debugging methods
  void DumpBuffer() const;
  void PrintInfo() const;

  std::string WaveformString( const int16_t channel ,
                              const unsigned capture ) const ;

public:
  int16_t device;// integer representing device in driver API

  int range;
  uint16_t triggerchannel;
  uint16_t triggerdirection;
  float    triggerlevel;
  unsigned triggerdelay;
  uint16_t triggerwait;

  unsigned timebase;// integer code to temporal spacing.
  int timeinterval;// temporal spacing in nano seconds.
  unsigned presamples;
  unsigned postsamples;// number of temporal samples for data collection.
  int maxsamples;// maximum number of time samples
  unsigned ncaptures;// Number of block capture for perform per function call
  int runtime;// storing runtime for Rapid block

private:
  std::vector<std::unique_ptr<int16_t[]> > bufferA;
  std::vector<std::unique_ptr<int16_t[]> > bufferB;
  std::unique_ptr<int16_t[]> overflowbuffer;

  // Helper functions for sanity check
  void findTimeInterval();// Running once and not changing;
};

#endif
