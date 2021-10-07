#ifndef DRS_HPP
#define DRS_HPP

#include "DRS.h"

#include <memory>
#include <string>
#include <vector>


class DRSContainer
{
public:
  void Init();
  void StartCollect();
  void ForceStop();

  // Setting commands
  void SetTrigger( const unsigned channel,
                   const double   level,
                   const unsigned direction,
                   const double   delay );
  void SetRate( const double frequency );
  void SetSamples( const unsigned );

  // Direct interfaces
  void               WaitReady();
  std::vector<float> GetWaveform( const unsigned channel );
  std::vector<float> GetTimeArray( const unsigned channel );

  // High level interfaces
  std::string WaveformStr( const unsigned channel );
  double      WaveformSum( const unsigned channel,
                           const unsigned intstart = -1,
                           const unsigned intstop  = -1,
                           const unsigned pedstart = -1,
                           const unsigned pedstop  = -1 );

  // Debugging methods
  void DumpBuffer( const unsigned channel );
  void TimeSlice( const unsigned channel );

  void RunCalib();

  int      TriggerChannel();
  int      TriggerDirection();
  double   TriggerDelay();
  double   TriggerLevel();
  double   GetRate();
  unsigned GetSamples();


  bool IsAvailable() const;
  bool IsReady();
  void CheckAvailable() const;

private:
  // Variables for handling the various handles.
  std::unique_ptr<DRS> drs;
  DRSBoard* board;

  // Time samples
  double triggerlevel;
  unsigned triggerchannel;
  int triggerdirection;
  double triggerdelay;
  unsigned samples;

// singleton related stuff.

private:
  // static variables for singleton class
  static std::unique_ptr<DRSContainer> _instance;
  // Hiding the initializer class.
  DRSContainer();
  DRSContainer( const DRSContainer& )  = delete;
  DRSContainer( const DRSContainer&& ) = delete;

public:
  // Destructor is still public since there is nothing special regarding the
  // variable memory management of the class instance.
  ~DRSContainer();// Destructor still bpu

  // Methods for accessing and creating the instance class.
  static DRSContainer& instance();
  static int           make_instance();
};


#endif
