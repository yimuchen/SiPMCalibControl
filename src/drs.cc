/**
 * @file drs.cc
 * @author Yi-Mu Chen
 * @brief A high level interface for the DRS4 serializer.
 *
 * Here we provide a simpler interface to interface to initialize the DRS4
 * oscilloscope with the default settings required for SiPM data collection, as
 * well as abstraction for the typical actions of pulse-like waveform
 * aquisition and waveform summing, and status report. This is basically a
 * stripped down and specialized method found in the DRS4 reference program[1]
 * that serves as the main reference of this file.
 *
 * The collection will always be in single-shot mode, with no exposure the
 * methods required to this setting. Notice that the DRS4 will not have a
 * timeout for single shot mode once collection is requested, so the user will
 * be responsible for making sure that the appropriate trigger is provided.
 *
 * [1] https://www.psi.ch/en/drs/software-download
 */
#include "drs.hpp"
#include "logger.hpp"

#include <iostream>
#include <stdexcept>
#include <unistd.h>

/**
 * @brief Initializing the DRS4 container in single shot mode, and external
 * triggers.
 *
 * As the reference program is a bit verbose, here we reduce the input to what
 * is needed for out single-shot operation. We also include explicit settings
 * commented out to make sure future development doesn't open certain settings
 * that is already known to cause issues by accident.
 */
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
  // DO NOT ENABLE TRANSPARENT MODE!!!
  // board->SetTranspMode( 1 );
  // board->SetDominoMode( 0 );// Singe shot mode
  // board->SetReadoutMode( 1 );// Read most recent

  /* set input range to -0.5V ... +0.5V */
  board->SetInputRange( 0 );

  // DO NOT ENABLE INTERNAL CLOCK CALIBRATION!!
  // board->EnableTcal( 1 );
  // By default setting to use the external trigger
  SetTrigger( 4,// Channel external trigger
              0.05,// Trigger on 0.05 voltage
              1,// Rising edge
              0 );// 0 nanosecond delay by default.
  // Additional two microsecond sleep for configuration to get through.
  usleep( 2 );
}


/**
 * @brief Waiting for the DRS4 to be ready for data transfer.
 *
 * This function will suspend the thread indefinitely until the DRS4 is ready
 * for data transfer operation. After the suspension, the data will always be
 * flushed to the main buffer (as this main program is only ever intended to be
 * done with the DRS4 running in single-shot mode).
 */
void
DRSContainer::WaitReady()
{
  CheckAvailable();
  while( board->IsBusy() ){usleep( 2 );
  } board->TransferWaves( 0, 8 );// Flush all waveforms into buffer.
}


/**
 * @brief Getting the time slice array for precision timing of a specific
 * channel.
 *
 * Notice that this only changes once a timing calibration is performed, so it
 * can be reused between calibration runs. However, it is found that the timing
 * variation from a regular interval deducted from the sample frequency is small
 * enough that this function is only included for the sake of debugging and
 * display. The timing returned is in units of nanoseconds.
 */
std::vector<float>
DRSContainer::GetTimeArray( const unsigned channel )
{
  static const unsigned len = 2048;
  float                 time_array[len];
  WaitReady();
  board->GetTime( 0, 2 * channel, board->GetTriggerCell( 0 ), time_array );
  return std::vector<float>( time_array, time_array+len );
}


/**
 * @brief Returning the last collected waveform as an array of floats
 *
 * This is a lowest level interface with the DRS4 API, and so no conversion
 * will be returned here, the return vector will always be a fixed length long
 * (2048). Conversion should be handled by the other functions.
 *
 * Notice that this function will wait indefinitely for the board to finish
 * data collection. So the user is responsible for making sure that the
 * appropriate trigger signal is sent.
 */
std::vector<float>
DRSContainer::GetWaveform( const unsigned channel )
{
  static const unsigned len = 2048;
  float                 waveform[len];
  WaitReady();

  // Notice that channel index 0-1 both correspond to the the physical
  // channel 1 input, and so on.
  int status = board->GetWave( 0, channel * 2, waveform );
  if( status ){
    throw std::runtime_error( "Error running DRSBoard::GetWave" );
  }
  return std::vector<float>( waveform, waveform+len );
}


/**
 * @brief Returning the latest collected waveform at specified channel in a
 * hex-string format.
 *
 * Each waveforma value is converted to a (signed) 16bit integer with 1bit
 * representing 0.1mV. The 16bit integer is then converted into hex-string
 * format and returned.
 */
std::string
DRSContainer::WaveformStr( const unsigned channel )
{
  const auto     waveform = GetWaveform( channel );
  const unsigned length   =
    std::min((unsigned)board->GetChannelDepth(), samples );
  std::string ans( 4 * length, '\0' );
  for( unsigned i = 0; i < length; ++i ){
    // Converting to 16 bit with 0.1mV as a ADC value.
    const int16_t raw  = waveform[i] / 0.1;
    const int8_t  dig0 = ( raw >> 12 ) & 0xf;
    const int8_t  dig1 = ( raw >> 8 )  & 0xf;
    const int8_t  dig2 = ( raw >> 4 )  & 0xf;
    const int8_t  dig3 = raw & 0xf;
    ans[4 * i+0] = dig0 <= 9 ?
                   '0'+dig0 :
                   'a'+( dig0 % 10 );
    ans[4 * i+1] = dig1 <= 9 ?
                   '0'+dig1 :
                   'a'+( dig1 % 10 );
    ans[4 * i+2] = dig2 <= 9 ?
                   '0'+dig2 :
                   'a'+( dig2 % 10 );
    ans[4 * i+3] = dig3 <= 9 ?
                   '0'+dig3 :
                   'a'+( dig3 % 10 );
  }
  return ans;
}


/**
 * @brief Returning the waveform of a given channel summed over the integration
 * window, with a pedestal subtraction if needed.
 *
 * The integration window and pedestal window is specified by sample indices,
 * so you will need to calculate the required window from the timing
 * information. The return will be single double for the waveform area in units
 * of mV x ns. Notice that timing information will *NOT* be used, as we simply
 * assuming perfect temporal spacing between the sampled values.
 *
 * In case you do not want to to perform pedestal subtraction, the starting the
 * stopping indices to the same value.
 */
double
DRSContainer::WaveformSum( const unsigned channel,
                           const unsigned _intstart,
                           const unsigned _intstop,
                           const unsigned _pedstart,
                           const unsigned _pedstop )
{
  const auto     waveform = GetWaveform( channel );
  const unsigned maxlen   = board->GetChannelDepth();
  double         pedvalue = 0;

  // Getting the pedestal value if required
  if( _pedstart != _pedstop ){
    const unsigned pedstart = std::max( unsigned(0), _pedstart );
    const unsigned pedstop  = std::min( maxlen, _pedstop );
    for( unsigned i = pedstart; i < pedstop; ++i ){
      pedvalue += waveform[i];
    }
    pedvalue /= (double)( pedstop-pedstart );
  }

  // Running the additional parsing.
  const unsigned intstart  = std::max( unsigned(0), _intstart );
  const unsigned intstop   = std::min( maxlen, _intstop );
  double         ans       = 0;
  const double   timeslice = 1.0 / GetRate();
  for( unsigned i = intstart; i < intstop; ++i ){
    ans += waveform[i];
  }
  ans -= pedvalue * ( intstop-intstart );
  ans *= -timeslice;// Negative to correct pulse direction
  return ans;
}


/**
 * @brief Printing the latest buffer collection results on the screen for
 * debugging.
 *
 * This will be the only time where the timing results will be displayed. The
 * waveform summation will not use the timing information.
 */
void
DRSContainer::DumpBuffer( const unsigned channel )
{
  static const std::string head = GREEN( "[DRSBUFFER]" );
  char                     print_line[256];// Display string;
  const auto               waveform   = GetWaveform( channel );
  const auto               time_array = GetTimeArray( channel );
  const unsigned           length     = GetSamples();
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


/**
 * @brief Setting the trigger
 *
 * For the channel, use 4 to set to external trigger. The level and direction
 * will only be used if the trigger channel is set to one of the readout
 * channels. Delay will always be in units of nanoseconds.
 */
void
DRSContainer::SetTrigger( const unsigned channel,
                          const double   level,
                          const unsigned direction,
                          const double   delay )
{
  CheckAvailable();
  board->EnableTrigger( 1, 0 );// Using hardware trigger
  board->SetTriggerSource( 1 << channel );
  triggerchannel = channel;

  // Certain trigger settings are only used for internal triggers.
  if( channel < 4 ){
    board->SetTriggerLevel( level );
    triggerlevel = level;
    board->SetTriggerPolarity( direction );
    triggerdirection = direction;
  }
  triggerdelay = delay;
  board->SetTriggerDelayNs( delay );

  // Sleeping to allow settings to settle.
  usleep( 500 );
}


/**
 * @brief Getting the trigger channel stored in object.
 */
int
DRSContainer::TriggerChannel()
{
  return triggerchannel;
}


/**
 * @brief Getting the trigger direction stored in object.
 */
int
DRSContainer::TriggerDirection()
{
  return triggerdirection;
}


/**
 * @brief Getting the trigger delay in the DRS instance.
 */
double
DRSContainer::TriggerDelay()
{
  return triggerdelay;
}


/**
 * @brief Getting the trigger level stored in object
 */
double
DRSContainer::TriggerLevel()
{
  return triggerlevel;
}


/**
 * @brief Setting the data sampling rate.
 *
 * Notice that this will not be the real sampling rate, the DRS will
 * automatically round to the closest available value.
 */
void
DRSContainer::SetRate( const double x )
{
  CheckAvailable();
  board->SetFrequency( x, true );
}


/**
 * @brief Getting the true sampling rate
 *
 * @return double
 */
double
DRSContainer::GetRate()
{
  CheckAvailable();
  double ans;
  board->ReadFrequency( 0, &ans );
  return ans;
}


/**
 * @brief Getting the number of sample to store.
 */
unsigned
DRSContainer::GetSamples()
{
  return std::min( (unsigned)board->GetChannelDepth(), samples );
}


/**
 * @brief Setting the number of values to store by default
 */
void
DRSContainer::SetSamples( const unsigned x )
{
  samples = x;
}


/**
 * @brief Starting a single-shot collection request.
 */
void
DRSContainer::StartCollect()
{
  CheckAvailable();
  board->StartDomino();
}


/**
 * @brief Forcing the collection to stop.
 */
void
DRSContainer::ForceStop()
{
  CheckAvailable();
  board->SoftTrigger();
}


/**
 * @brief Checking that a DRS4 is available for operation. Throw exception if
 * not.
 */
void
DRSContainer::CheckAvailable() const
{
  if( !IsAvailable() ){
    throw std::runtime_error( "DRS4 board is not available" );
  }
}


/**
 * @brief True/False flag for whether the DRS4 is available for operation.
 */
bool
DRSContainer::IsAvailable() const
{
  return drs != nullptr && board != nullptr;
}


/**
 * @brief Simple check for whether data collection has finished.
 */
bool
DRSContainer::IsReady()
{
  return !board->IsBusy();
}


/**
 * @brief Simple wrapper function for running the calibration at the current
 * settings.
 *
 * This C++ function will assume that the DRS is in a correct configuration to
 * be calibrated (all inputs disconnected). Additional user instructions will
 * be handled by the python part.
 */
void
DRSContainer::RunCalib()
{
  // Dummy class for overloading the callback function
  class DummyCallback : public DRSCallback
  {
public:
    virtual void Progress( int ){} // Do nothing
  };
  CheckAvailable();

  // Running the time calibration and voltage calibration each time the DRS is
  // initialized.
  DummyCallback _d;
  board->SetFrequency( 2.0, true );
  board->CalibrateTiming( &_d );
  board->SetRefclk( 0 );
  board->CalibrateVolt( &_d );

  // After running, we will need to reset the board trigger configurations
  // By default setting to use the external trigger
  SetTrigger( TriggerChannel(),// Channel external trigger
              TriggerLevel(),// Trigger on 0.05 voltage
              TriggerDirection(),// Rising edge
              TriggerDelay() );// 0 nanosecond delay by default.
}


IMPLEMENT_SINGLETON( DRSContainer );
DRSContainer::DRSContainer() :
  board( nullptr ){}
DRSContainer::~DRSContainer()
{
  printf( "Deallocating the DRS controller\n" );
}
