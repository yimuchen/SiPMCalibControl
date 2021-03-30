#include "DRS.h"

#include "logger.hpp"

#include <iostream>
#include <memory>
#include <stdexcept>
#include <unistd.h>

class DRSContainer
{
public:
  DRSContainer();
  // DRSContainer( const DRSContainer& )  = delete;
  // DRSContainer( const DRSContainer&& ) = delete;
  ~DRSContainer();

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


  // Main output samples
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
  std::unique_ptr<DRS> drs;
  DRSBoard* board;

  // Time samples

  double triggerlevel;
  unsigned triggerchannel;
  int triggerdirection;
  unsigned samples;
};

DRSContainer::DRSContainer() :
  board( nullptr )
{}

void
DRSContainer::Init()
{
  char str[256];
  char errmsg[2048];

  drs = std::make_unique<DRS>();
  if( drs->GetError( str, sizeof( str ) ) ){
    drs = nullptr;
    sprintf( errmsg, "Error created DRS instance: %s", str );
    throw std::runtime_error( errmsg );
  }

  if( !drs->GetNumberOfBoards() ){
    throw std::runtime_error( "No DRS boards found" );
  }
  // Only getting the first board for now.
  board = drs->GetBoard( 0 );
  board->Init();

  printf( "Found DRS%d board on USB, serial #%04d, firmware revision %5d\n",
    board->GetDRSType(),
    board->GetBoardSerialNumber(),
    board->GetFirmwareVersion() );


  // 2 microsecond sleep to allow for settings to settle down
  usleep( 2 );
  // Running the various common settings required for the SiPM calibration
  // board->SetChannelConfig( 0, 8, 8 );// 1024 binning
  board->SetFrequency( 2.0, true );// Running at target 2GHz sample rate.

  // enable transparent mode needed for analog trigger
  // DO NOT ENABLE THIS!!!
  // board->SetTranspMode( 1 );

  // board->SetDominoMode( 0 );// Singe shot mode
  // board->SetReadoutMode( 1 );// Read most recent

  /* set input range to -0.5V ... +0.5V */
  board->SetInputRange( 0 );

  // use following line to turn on the internal 100 MHz clock connected to all
  // channels. DO NOT ENABLE THIS!!
  // board->EnableTcal( 1 );

  // By default setting to use the external trigger
  SetTrigger( 4,// Channel external trigger
    0.05,// Trigger on 0.05 voltage
    1,// Rising edge
    0 );// 0 nanosecond delay by default.

  // Additional two microsecond sleep for configuration to get through.
  usleep( 2 );


}

DRSContainer::~DRSContainer()
{
  printf( "Deallocating the DRS controller\n" );
}

void
DRSContainer::TimeSlice( const unsigned channel )
{
  CheckAvailable();
  float time_array[2048];

  // Waiting indefinitely for the waveform to be collected
  while( board->IsBusy() ){
    usleep( 2 );
  }

  // Getting all channels
  board->TransferWaves( 0, 8 );
  /* read time (X) array of first channel in ns */
  board->GetTime( 0, 2*channel, board->GetTriggerCell( 0 ), time_array );

  for( int i = 0; i < 12*20; i = i+20 ){
    printf( "%7.2f ", time_array[i] );
  }

  printf( "...\n" );
  fflush( stdout );

}

/**
 * @brief Returning a string of length 4xSamples.
 */
std::string
DRSContainer::WaveformStr( const unsigned channel )
{
  CheckAvailable();

  // Waiting indefinitely for the waveform to be collected
  while( board->IsBusy() ){
    usleep( 2 );
  }

  // Getting the waveform.
  float waveform[2048];

  // Transfere all 4x2 channel waveforms
  board->TransferWaves( 0, 8 );

  // Notice that channel index 0-1 both correspond to the the physical
  // channel 1 input, so this should be find.
  int status = board->GetWave( 0
                             , channel *2
                             , waveform );

  if( status ){
    throw std::runtime_error( "Error running DRSBoard::GetWave" );
  }

  const unsigned length = std::min( (unsigned)board->GetChannelDepth()
                                  , samples );
  std::string ans( 4 * length, '\0' );

  for( unsigned i = 0; i < length; ++i ){
    // Converting to 16 bit with 0.1mV as a ADC value.
    const int16_t raw = waveform[i] / 0.1;
    const int8_t dig0 = ( raw >> 12 ) & 0xf;
    const int8_t dig1 = ( raw >> 8 )  & 0xf;
    const int8_t dig2 = ( raw >> 4 )  & 0xf;
    const int8_t dig3 = raw & 0xf;
    ans[4*i+0] = dig0 <= 9 ? '0' + dig0 : 'a' + ( dig0 % 10 );
    ans[4*i+1] = dig1 <= 9 ? '0' + dig1 : 'a' + ( dig1 % 10 );
    ans[4*i+2] = dig2 <= 9 ? '0' + dig2 : 'a' + ( dig2 % 10 );
    ans[4*i+3] = dig3 <= 9 ? '0' + dig3 : 'a' + ( dig3 % 10 );
  }

  return ans;
}

/**
 * @brief Returning the waveform of a given channel summed over the integration
 * window, with a pedestal subtraction if needed.
 */
double
DRSContainer::WaveformSum( const unsigned channel,
                           const unsigned _intstart,
                           const unsigned _intstop,
                           const unsigned _pedstart,
                           const unsigned _pedstop )
{
  CheckAvailable();

  while( board->IsBusy() ){
    usleep( 2 );
  }

  float waveform[2048];
  board->TransferWaves( 0, 8 );
  int status = board->GetWave( 0, channel*2, waveform );

  if( status ){
    throw std::runtime_error( "Error running DRSBoard::GetWave" );
  }

  double pedvalue = 0;

  // Getting the pedestal value if
  if( _pedstart != _pedstop ){
    const unsigned pedstart = std::max( unsigned(0), _pedstart );
    const unsigned pedstop  = std::min( (unsigned)board->GetChannelDepth()
                                      , _pedstop );


    for( unsigned i = pedstart; i < pedstop; ++i ){
      pedvalue += waveform[i];
    }

    pedvalue /= (double)( pedstop - pedstart );
  }

  // Running the additional parsing.
  const unsigned intstart = std::max( unsigned(0), _intstart );
  const unsigned intstop  = std::min( (unsigned)board->GetChannelDepth()
                                    , _intstop );

  double ans             = 0;
  const double timeslice = 1.0/GetRate();

  for( unsigned i = intstart; i < intstop; ++i ){
    ans += ( waveform[i] - pedvalue )*timeslice;
  }

  return ans;

}

void
DRSContainer::DumpBuffer( const unsigned channel )
{
  CheckAvailable();
  // Static variable for getting stuff.
  static const std::string head = GREEN( "[DRSBUFFER]" );

  // Getting the waveform. and timing information
  float waveform[2048];
  float time_array[2048];
  char print_line[256];

  // Waiting indefinitely for the waveform to be collected
  while( board->IsBusy() ){
    usleep( 2 );
  }

  // Transfere all 4x2 channel waveforms
  board->TransferWaves( 0, 8 );

  // Notice that channel index 0-1 both correspond to the the physical
  // channel 1 input, so this should be find.
  int status = board->GetWave( 0
                             , channel *2
                             , waveform );

  if( status ){
    throw std::runtime_error( "Error running DRSBoard::GetRawWave" );
  }

  // For the detailed dump, we will be using the precision timing information,
  // note that precision timing information will note be used stored in the
  // output waveform.

  board->GetTime( 0, 2*channel, board->GetTriggerCell( 0 ), time_array );

  const unsigned length = std::min( (unsigned)board->GetChannelDepth()
                                  , samples );

  sprintf( print_line, "%7s | Channel %d [mV]", "Time", channel );
  printmsg( head, print_line );

  for( unsigned i = 0; i < length; ++i ){
    sprintf( print_line, "%7.3lf | %7.2lf", time_array[i], waveform[i] );
    printmsg( head, print_line );
  }

  // Additional two empty lines for aesthetic reasons.
  printmsg( "" );
  printmsg( "" );
}

void
DRSContainer::SetTrigger( const unsigned channel,
                          const double   level,
                          const unsigned direction,
                          const double   delay  )
{
  CheckAvailable();
  board->EnableTrigger( 1, 0 );// Using hardware trigger
  board->SetTriggerSource( 1 << channel );
  triggerchannel = channel;

  // Certain trigger settings are only used for internal triggers.
  if( channel < 4 ){
    printf( "Setting trigger level %lf\n", level );
    board->SetTriggerLevel( level );
    triggerlevel = level;
    board->SetTriggerPolarity( direction );
    triggerdirection = direction;
  }

  printf( "Setting trigger delay %lf\n", delay );
  board->SetTriggerDelayNs( delay );

  // Sleeping to allow settings to settle.
  usleep( 500 );
}

int
DRSContainer::TriggerChannel()
{
  return triggerchannel;
}

int
DRSContainer::TriggerDirection()
{
  return triggerdirection;
}

double
DRSContainer::TriggerDelay()
{
  CheckAvailable();
  return board->GetTriggerDelayNs();
}

double
DRSContainer::TriggerLevel()
{
  return triggerlevel;
}


void
DRSContainer::SetRate( const double x )
{
  CheckAvailable();
  board->SetFrequency( x, true );
}

double
DRSContainer::GetRate()
{
  CheckAvailable();
  double ans;
  board->ReadFrequency( 0, &ans );
  return ans;
}

unsigned
DRSContainer::GetSamples()
{
  return samples;
}

void
DRSContainer::SetSamples( const unsigned x )
{
  samples = x;
}

void
DRSContainer::StartCollect()
{
  CheckAvailable();
  board->StartDomino();
  // board->ReadFrequency( 0, &freq );
}

void
DRSContainer::ForceStop()
{
  CheckAvailable();
  board->SoftTrigger();
}

void
DRSContainer::CheckAvailable() const
{
  if( drs == nullptr || board == nullptr ){
    throw std::runtime_error( "DRS4 board is not available" );
  }
}

bool
DRSContainer::IsAvailable() const
{
  return drs.get() != nullptr;
}

bool
DRSContainer::IsReady()
{
  return !board->IsBusy();
}

/**
 * @brief Simple wrapper function for running the calibration at the current
 * settings. This C++ function will assume that the DRS is in a correct
 * configuration to be calibrated (all inputs disconnected). Additional user
 * instructions will be handled by the python part.
 */
void
DRSContainer::RunCalib()
{
  // Dummy class for overloading the callback function
  class DummyCallback : public DRSCallback
  {
public:
    virtual void Progress( int ){};// Do nothing
  };

  CheckAvailable();

  // Running the time calibration and voltage calibration each time the DRS is
  // initialized.
  DummyCallback _d;
  board->SetFrequency( 2.0, true );
  board->CalibrateTiming( &_d );

  board->SetRefclk( 0 );
  board->CalibrateVolt( &_d );
}


#ifndef STANDALONE
#include <boost/python.hpp>
#include <boost/python/def.hpp>

BOOST_PYTHON_MODULE( drs )
{
  boost::python::class_<DRSContainer, boost::noncopyable>( "DRS" )
  .def( "init",              &DRSContainer::Init )
  .def( "timeslice",         &DRSContainer::TimeSlice )
  .def( "startcollect",      &DRSContainer::StartCollect )
  .def( "forcestop",         &DRSContainer::ForceStop )
  // Trigger related stuff
  .def( "set_trigger",       &DRSContainer::SetTrigger )
  .def( "trigger_channel",   &DRSContainer::TriggerChannel )
  .def( "trigger_direction", &DRSContainer::TriggerDirection )
  .def( "trigger_level",     &DRSContainer::TriggerLevel )
  .def( "trigger_delay",     &DRSContainer::TriggerDelay )

  // Collection related stuff
  .def( "set_samples",       &DRSContainer::SetSamples )
  .def( "samples",           &DRSContainer::GetSamples )
  .def( "set_rate",          &DRSContainer::SetRate )
  .def( "rate",              &DRSContainer::GetRate )

  .def( "is_available",      &DRSContainer::IsAvailable )
  .def( "is_ready",          &DRSContainer::IsReady )
  .def( "waveformstr",       &DRSContainer::WaveformStr )
  .def( "waveformsum",       &DRSContainer::WaveformSum )
  .def( "dumpbuffer",        &DRSContainer::DumpBuffer )
  .def( "run_calibrations",  &DRSContainer::RunCalib   )
  ;
}

#endif
