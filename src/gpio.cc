#include "gpio.hpp"

#include <cmath>
#include <fcntl.h>
#include <linux/i2c-dev.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include <deque>
#include <queue>
#include <stdexcept>

// Defining the static variables to be exposed to python
const uint8_t GPIO::ADS_RANGE_6V   = 0x0;
const uint8_t GPIO::ADS_RANGE_4V   = 0x1;
const uint8_t GPIO::ADS_RANGE_2V   = 0x2;
const uint8_t GPIO::ADS_RANGE_1V   = 0x3;
const uint8_t GPIO::ADS_RANGE_p5V  = 0x4;
const uint8_t GPIO::ADS_RANGE_p25V = 0x5;

const uint8_t GPIO::ADS_RATE_8SPS   = 0x0;
const uint8_t GPIO::ADS_RATE_16SPS  = 0x1;
const uint8_t GPIO::ADS_RATE_32SPS  = 0x2;
const uint8_t GPIO::ADS_RATE_64SPS  = 0x3;
const uint8_t GPIO::ADS_RATE_128SPS = 0x4;
const uint8_t GPIO::ADS_RATE_250SPS = 0x5;
const uint8_t GPIO::ADS_RATE_475SPS = 0x6;
const uint8_t GPIO::ADS_RATE_860SPS = 0x7;

void
GPIO::Init()
{
  try {
    gpio_light   = InitGPIOPin(   light_pin, WRITE );
    gpio_trigger = InitGPIOPin( trigger_pin, WRITE );
    gpio_spare   = InitGPIOPin(   spare_pin, WRITE );

    InitPWM();

    if( gpio_adc != UNOPENED ){
      CloseI2CFlush();
    }

    gpio_adc = InitI2C();
    if( gpio_adc != OPEN_FAILED && gpio_adc != UNOPENED ){
      PushADCSetting();
      InitI2CFlush();
    }
  } catch( std::runtime_error& e ){
    // For local testing, this start the I2C monitoring flush even if
    // Something failed, (The ADC readout will just be a random stream)
    InitI2CFlush();

    // Passing error message onto higher functions
    throw e;
  }
}

GPIO::GPIO() :
  gpio_trigger( UNOPENED ),
  gpio_light( UNOPENED ),
  gpio_spare( UNOPENED ),
  gpio_adc( UNOPENED ),
  adc_range( ADS_RANGE_4V ),
  adc_rate( ADS_RATE_250SPS ),
  adc_channel( 0 ),
  i2c_flush( false )
{
  pwm_enable[0] = UNOPENED;
  pwm_duty[0]   = UNOPENED;
  pwm_period[0] = UNOPENED;
  pwm_enable[1] = UNOPENED;
  pwm_duty[1]   = UNOPENED;
  pwm_period[1] = UNOPENED;

  i2c_flush_array[0] = 2500.0;
  i2c_flush_array[1] = 2500.0;
  i2c_flush_array[2] = 2500.0;
  i2c_flush_array[3] = 2500.0;

  reference_voltage[0] = 5000.0;
  reference_voltage[1] = 5000.0;
  reference_voltage[2] = 5000.0;
  reference_voltage[3] = 5000.0;

  pwm_duty_value[0] = 0.5;
  pwm_duty_value[1] = 0.5;
}

GPIO::~GPIO()
{
  // Turning off LED light when the process has ended.
  printf( "Closing GPIO pins for the light\n" );
  if( gpio_light >= NORMAL_PTR ){
    LightsOff();
    close( gpio_light );
    CloseGPIO( light_pin );
  }

  printf( "Closing GPIO pins for the trigger\n" );
  if( gpio_trigger >= NORMAL_PTR ){
    close( gpio_trigger );
    CloseGPIO( trigger_pin );
  }

  printf( "Closing GPIo pins for the PWM\n" );
  ClosePWM();

  printf( "Closing the I2C interface\n" );
  if( gpio_adc >= NORMAL_PTR ){
    CloseI2CFlush();
    close( gpio_adc );
  } else {
    CloseI2CFlush();
  }
}

// ******************************************************************************
// High level function for trigger control
// ******************************************************************************
void
GPIO::Pulse( const unsigned n, const unsigned wait ) const
{
  if( gpio_trigger == OPEN_FAILED ){
    throw std::runtime_error( "GPIO for trigger pin is not initialized" );
  }

  for( unsigned i = 0; i < n; ++i ){
    GPIOWrite( gpio_trigger, HI );
    std::this_thread::sleep_for( std::chrono::microseconds( 1 ) );
    GPIOWrite( gpio_trigger, LOW );
    std::this_thread::sleep_for( std::chrono::microseconds( wait ) );
  }
}

// ******************************************************************************
// High level function for light control
// ******************************************************************************
void
GPIO::LightsOn() const
{
  if( gpio_light == OPEN_FAILED ){
    throw std::runtime_error( "GPIO for light pin is not initialized" );
  }

  GPIOWrite( gpio_light, HI );
}

void
GPIO::LightsOff() const
{
  if( gpio_light == OPEN_FAILED ){
    throw std::runtime_error( "GPIO for light pin is not initialized" );
  }
  GPIOWrite( gpio_light, LOW );
}

void
GPIO::SpareOn() const
{
  if( gpio_spare == OPEN_FAILED ){
    throw std::runtime_error( "GPIO for spare pin is not initialized" );
  }
  GPIOWrite( gpio_spare, HI );
}

void
GPIO::SpareOff() const
{
  if( gpio_spare == OPEN_FAILED ){
    throw std::runtime_error( "GPIO for spare pin is not initialized" );
  }

  GPIOWrite( gpio_spare, LOW );
}

// ******************************************************************************
// GPIO Settings related functions
// ******************************************************************************
int
GPIO::InitGPIOPin( const int pin, const unsigned direction )
{
  static constexpr unsigned buffer_length = 35;
  unsigned write_length;
  char buffer[buffer_length];
  char path[buffer_length];
  char errmsg[1024];

  int fd = open( "/sys/class/gpio/export", O_WRONLY );
  if( fd == OPEN_FAILED ){
    sprintf( errmsg, "Failed to open /sys/class/gpio/export" );
    throw std::runtime_error( errmsg );
  }
  write_length = snprintf( buffer, buffer_length, "%u", pin );
  write( fd, buffer, write_length );
  close( fd );

  // Small pause for system settings to finish rippling
  std::this_thread::sleep_for( std::chrono::milliseconds( 100 ) );

  // Setting direction.
  snprintf( path, buffer_length, "/sys/class/gpio/gpio%d/direction", pin );

  // Waiting for the sysfs to generated the corresponding file
  while( access( path, F_OK ) == -1 ){
    std::this_thread::sleep_for( std::chrono::milliseconds( 100 ) );
  }

  fd = ( direction == READ ) ? open( path, O_WRONLY ) : open( path, O_WRONLY );
  if( fd  == OPEN_FAILED ){
    sprintf( errmsg, "Failed to open gpio [%d] direction! [%s]", pin, path );
    throw std::runtime_error( errmsg );
  }

  int status = write( fd
                    , direction == READ ? "in" : "out"
                    , direction == READ ? 2    : 3 );
  if( status == IO_FAILED ){
    sprintf( errmsg, "Failed to set gpio [%d] direction!", pin );
    throw std::runtime_error( errmsg );
  }
  close( fd );

  // Opening GPIO PIN
  snprintf( path, buffer_length, "/sys/class/gpio/gpio%d/value", pin );
  fd = ( direction == READ ) ? open( path, O_RDONLY ) : open( path, O_WRONLY );
  if( fd == OPEN_FAILED ){
    sprintf( errmsg, "Failed to open gpio [%d] value! [%s]", pin, path );
    throw std::runtime_error( errmsg );
  }

  return fd;
}

int
GPIO::GPIORead( const int fd )
{
  char value_str[3];
  if( read( fd, value_str, 3 ) == IO_FAILED ){
    throw std::runtime_error( "Failed to read gpio value!" );
  }
  return atoi( value_str );
}

void
GPIO::GPIOWrite( const int fd, const unsigned val )
{
  if( write( fd, LOW == val ? "0" : "1", 1 ) == IO_FAILED ){
    throw std::runtime_error( "Failed to write gpio value!" );
  }
}

void
GPIO::CloseGPIO( const int pin )
{
  static constexpr unsigned buffer_length = 3;
  unsigned write_length;
  char buffer[buffer_length];
  int fd = open( "/sys/class/gpio/unexport", O_WRONLY );
  if( fd == OPEN_FAILED ){
    throw std::runtime_error( "Failed to open un-export for writing!" );
  }

  write_length = snprintf( buffer, buffer_length, "%d", pin );
  write( fd, buffer, write_length );

  close( fd );
}

// ******************************************************************************
// PWM related stuff
// ******************************************************************************
void
GPIO::InitPWM()
{
  char errmsg[1024];

  int fd = open( "/sys/class/pwm/pwmchip0/export", O_WRONLY );
  if( fd == OPEN_FAILED ){
    sprintf( errmsg, "Failed to open /sys/class/pwm/pwmchip0/export" );
    pwm_enable[0] = -1;// Flagging the PWM stuff as unopened.
    throw std::runtime_error( errmsg );
  }
  write( fd, "0", 1 );
  write( fd, "1", 1 );

  // Waiting for the sysfs to generated the corresponding file
  while( access( "/sys/class/pwm/pwmchip0/pwm0/enable", F_OK ) == OPEN_FAILED ){
    printf( "Waiting for /sys/class/pwm/pwmchip0/pwm0/enable" );
    std::this_thread::sleep_for( std::chrono::milliseconds( 100 ) );
  }

  while( access( "/sys/class/pwm/pwmchip0/pwm1/enable", F_OK ) == OPEN_FAILED ){
    printf( "Waiting for /sys/class/pwm/pwmchip0/pwm1/enable" );
    std::this_thread::sleep_for( std::chrono::milliseconds( 100 ) );
  }

  // Small loop to continuously try to open the PWM interface. If the interface
  // cannot be opened. An exception would have been raised at the start of the
  // function.
  do{
    pwm_enable[0] = open( "/sys/class/pwm/pwmchip0/pwm0/enable",      O_WRONLY );
    pwm_duty[0]   = open( "/sys/class/pwm/pwmchip0/pwm0/duty_cycle",  O_WRONLY );
    pwm_period[0] = open( "/sys/class/pwm/pwmchip0/pwm0/period",      O_WRONLY );

    pwm_enable[1] = open( "/sys/class/pwm/pwmchip0/pwm0/enable",      O_WRONLY );
    pwm_duty[1]   = open( "/sys/class/pwm/pwmchip0/pwm0/duty_cycle",  O_WRONLY );
    pwm_period[1] = open( "/sys/class/pwm/pwmchip0/pwm0/period",      O_WRONLY );
    std::this_thread::sleep_for( std::chrono::milliseconds( 100 ) );
  }while( pwm_enable[0] == UNOPENED || pwm_enable[0] == OPEN_FAILED );

  if( pwm_enable[0] == OPEN_FAILED ){
    sprintf( errmsg, "Failed to open /sys/class/pwm/pwmchip0/pwm0/enable" );
    throw std::runtime_error( errmsg );
  }
  close( fd );
}

void
GPIO::ClosePWM()
{
  char errmsg[1024];

  if( pwm_enable[0] != UNOPENED ){
    for( unsigned channel = 0; channel <= 1; channel++ ){
      write( pwm_enable[channel], "0", 1 );
      close( pwm_enable[channel] );
      close( pwm_duty[channel] );
      close( pwm_period[channel] );

    }

    sprintf( errmsg, "/sys/class/pwm/pwmchip0/unexport" );
    int fd = open( errmsg, O_WRONLY );
    if( fd == OPEN_FAILED ){
      sprintf( errmsg, "Failed to open /sys/class/pwm/pwmchip0/unexport" );
      throw std::runtime_error( errmsg );
    }
    write( fd, "0", 1 );
    write( fd, "1", 1 );
  }
}


void
GPIO::SetPWM( const unsigned c,
              const double   dc,
              const double   f )
{
  // Channel 0 is Physical PIN 12  (GPIO pin 1/ALT5 mode in `gpio readall`)
  // Channel 1 is Physical PIN 35  (GPIO pin 24/ALT5 mode in `gpio readall`)

  // Limiting range
  const float frequency  = std::min( 1e5, f );
  const float duty_cycle = std::min( 1.0, std::max( 0.0, dc ) );
  const unsigned channel = std::min( unsigned(1), c );

  // Time is in units of nano seconds
  const unsigned period = 1e9 / frequency;
  const unsigned duty   = period * duty_cycle;

  char duty_str[10];
  char period_str[10];
  char errmsg[1024];
  unsigned duty_len   = sprintf( duty_str,    "%u", duty );
  unsigned period_len = sprintf( period_str,  "%u", period );

  if( pwm_enable[channel] == OPEN_FAILED ){
    sprintf( errmsg, "Failed to open /sys/class/pwm/pwmchip%u settings", c );
    throw std::runtime_error( errmsg );
  } else if( pwm_enable[channel] == UNOPENED ){
    // In the case that the PWM is unopened. Simply modify the previous
    // The content of the system
    if( channel == 0 ){
      i2c_flush_array[2] = duty_cycle * 5000.0;
    } else if( channel == 1 ){
      i2c_flush_array[3] = duty_cycle * 5000.0;
    }

  } else {
    write( pwm_enable[channel], "0",        1          );
    write( pwm_period[channel], period_str, period_len );
    write( pwm_duty[channel],   duty_str,   duty_len   );
    write( pwm_enable[channel], "1",        1          );
  }

  // Storing the PWM value for external reference.
  pwm_duty_value[channel] = duty_cycle;
}

float
GPIO::GetPWM( const unsigned c )
{
  const unsigned channel = std::min( unsigned(1), c );
  return pwm_duty_value[channel];
}


// ******************************************************************************
// I2C related functions
// Main reference:http://www.bristolwatch.com/rpi/ads1115.html
// ******************************************************************************
float
GPIO::ReadADC( const unsigned channel ) const
{
  return i2c_flush_array[channel];
}

void
GPIO::SetADCRange( const int range )
{
  if( adc_range  != range ){
    adc_range = range;
    PushADCSetting();
  }
}

void
GPIO::SetADCRate( const int rate )
{
  if( rate != adc_rate ){
    adc_rate = rate;
    PushADCSetting();
  }
}

int
GPIO::InitI2C()
{
  char errmsg[1024];
  int fd = open( "/dev/i2c-1", O_RDWR );
  // open device
  if( fd == OPEN_FAILED ){
    sprintf( errmsg, "Error: Couldn't open i2c device! %s", "/dev/i2c-1" );
    throw std::runtime_error( errmsg );
  }

  // connect to ADS1115 as i2c slave
  if( ioctl( fd, I2C_SLAVE, 0x48 ) == IO_FAILED ){
    sprintf( errmsg, "Error: Couldn't find i2c device on address [%d]!", 0x48 );
    throw std::runtime_error( errmsg );
  }

  return fd;
}

void
GPIO::PushADCSetting()
{
  const uint8_t channel = ( adc_channel & 0x3 ) | ( 0x1 << 2 );
  // channel should be compared with GND
  const uint8_t range = ( adc_range & 0x7 );
  const uint8_t rate  = ( adc_rate  & 0x7 );

  uint8_t write_buffer[3] = {
    1,// First register bit is always 1,
    // Configuration byte 1
    // Always  | MUX bits     | PGA bits    | MODE (always continuous)
    // 1       | x    x    x  | x   x   x   | 0
    ( 0x1 << 7 | channel << 4 |  range << 1 | 0x0 ),
    // Configuration byte 0
    // DR bits |  COM BITS (Leave as default)
    // x x x   | 0 0  0 1 1
    ( rate << 5  | 0b00011 )
  };
  uint8_t read_buffer[2] = {0};

  // Write and wait for OK signal.
  if( write( gpio_adc, write_buffer, 3 ) != 3 ){
    throw std::runtime_error( "Error writing setting to i2C device" );
  }

  std::this_thread::sleep_for( std::chrono::milliseconds( 100 ) );

  // Set for reading
  read_buffer[0] = 0;
  if( write( gpio_adc, read_buffer, 1 ) != 1 ){
    throw std::runtime_error( "Error setting to i2C device to read mode" );
  }
}

int16_t
GPIO::ADCReadRaw()
{
  uint8_t read_buffer[2] = {0};
  int16_t ans;

  read( gpio_adc, read_buffer, 2 );
  ans = read_buffer[0] << 8 | read_buffer[1];

  return ans;
}


float
GPIO::ReadNTCTemp( const unsigned channel ) const
{
  // Standard values for NTC resistors used in circuit;
  static const float T_0 = 25 + 273.15;
  static const float R_0 = 10000;
  static const float B   = 3500;

  // Standard operation values for biasing circuit
  static const float R_ref = 10000;

  // Dynamic convertion
  const float V_total = reference_voltage[channel];
  const float v       = ReadADC( channel );
  const float R       = R_ref * v / ( V_total - v );

  // Temperature equation from Steinhart–Hart equation.
  // 1/T = 1/T0 + 1/B * ln(R/R0)
  return ( T_0 * B )/( B + T_0* std::log( R/R_0 ) ) - 273.15;
}

float
GPIO::ReadRTDTemp( const unsigned channel ) const
{
  // Typical value of RTDs in circuit
  static const float R_0 = 10000;
  static const float T_0 = 273.15;
  static const float a   = 0.003916;

  // standard operation values for biasing circuit
  static const float R_ref = 10000;

  // Dynamic conversion
  const float V_total = reference_voltage[channel];
  const float v       = ReadADC( channel );
  const float R       = R_ref * v / ( V_total -v );

  // Temperature conversion is simply
  // R = R_0 (1 + a (T - T0))
  return T_0 + ( R - R_0 )/( R_0 * a ) - 273.15;
}

void
GPIO::SetReferenceVoltage( const unsigned channel, const float val )
{
  reference_voltage[channel] = val;
}

void
GPIO::FlushLoop( std::atomic<bool>& i2d_flush )
{
  while( i2c_flush == true ){
    if( gpio_adc >= NORMAL_PTR ){
      for( unsigned channel = 0; channel < 4; ++channel ){
        adc_channel = channel;
        try {// This is incase the GPIO interface is open but not addressable
          PushADCSetting();

          const int16_t adc   = ADCReadRaw();
          const uint8_t range = adc_range& 0x7;
          const float conv    = range == ADS_RANGE_6V  ? 6144.0 / 32678.0 :
                                range == ADS_RANGE_4V  ? 4096.0 / 32678.0 :
                                range == ADS_RANGE_2V  ? 2048.0 / 32678.0 :
                                range == ADS_RANGE_1V  ? 1024.0 / 32678.0 :
                                range == ADS_RANGE_p5V ?  512.0 / 32678.0 :
                                256.0 / 32678.0;
          i2c_flush_array[channel] = adc * conv;
          std::this_thread::sleep_for( std::chrono::milliseconds( 100 ) );
        } catch( std::exception& e ){
          i2c_flush_array[0] = i2c_flush_array[0];
          i2c_flush_array[1] = i2c_flush_array[1];
          i2c_flush_array[2] = i2c_flush_array[2];
          i2c_flush_array[3] = i2c_flush_array[3];
        }
      }
    } else {
      i2c_flush_array[0] = i2c_flush_array[0];
      i2c_flush_array[1] = i2c_flush_array[1];
      i2c_flush_array[2] = i2c_flush_array[2];
      i2c_flush_array[3] = i2c_flush_array[3];
    }

    std::this_thread::sleep_for( std::chrono::milliseconds( 50 ) );
  }
}

void
GPIO::InitI2CFlush()
{
  i2c_flush        = true;
  i2c_flush_thread = std::thread( [this] {
    this->FlushLoop( std::ref( i2c_flush ) );
  } );
}

void
GPIO::CloseI2CFlush()
{
  if( i2c_flush == true ){
    i2c_flush = false;
    i2c_flush_thread.join();
  }
}

// ******************************************************************************
// Simple parser of status from file pointer results
// ******************************************************************************
bool
GPIO::StatusGPIO() const
{
  return gpio_trigger >= NORMAL_PTR &&
         gpio_light   >= NORMAL_PTR &&
         gpio_spare   >= NORMAL_PTR;
}

bool
GPIO::StatusADC() const
{
  return gpio_adc >= NORMAL_PTR;
}

bool
GPIO::StatusPWM() const
{
  return pwm_enable[0] >= NORMAL_PTR &&
         pwm_duty[0]   >= NORMAL_PTR &&
         pwm_period[0] >= NORMAL_PTR &&
         pwm_enable[1] >= NORMAL_PTR &&
         pwm_duty[1]   >= NORMAL_PTR &&
         pwm_period[1] >= NORMAL_PTR;
}


/// Singleton stuff
std::unique_ptr<GPIO> GPIO::_instance = nullptr;

GPIO&
GPIO::instance()
{
  return *_instance;
}

int
GPIO::make_instance()
{
  if( _instance == nullptr ){
    _instance.reset( new GPIO() );
  }
  return 0;
}

static const int __make_instance_call = GPIO::make_instance();
