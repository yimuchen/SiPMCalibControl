#include <cmath>
#include <fcntl.h>
#include <linux/i2c-dev.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include <array>
#include <deque>
#include <queue>
#include <stdexcept>
#include <thread>

template<typename T, int maxlength, typename Container = std::deque<T> >
class FixedQueue : public std::queue<T, Container>
{
public:
  void push( const T& value )
  {
    if( this->size() == maxlength ){
      this->c.pop_front();
    }
    std::queue<T, Container>::push( value );
  }
};


class GPIO
{
public:
  GPIO();
  ~GPIO();

  void Init();

  // High level functions using GPIO interface
  void Pulse( const unsigned n, const unsigned wait ) const;
  void LightsOn() const;
  void LightsOff() const;

  // High level function using PWM interface
  void SetPWM( const unsigned channel,
               const double   duty_cycle,
               const double   frequency );

  // High level functions for I2C ADC chip interface
  void  SetADCRange( const int );
  void  SetADCRate( const int );
  float ReadADC( const unsigned channel );
  float ReadNTCTemp( const unsigned channel );
  float ReadRTDTemp( const unsigned channel );

  // On the raspberry PI, these pins correspond to the BCM pin from
  // wiringPi's `gpio readall` command
  static constexpr unsigned trigger_pin = 21;// PHYS PIN 40
  static constexpr unsigned light_pin   = 26; // PHYS PIN 37

  static constexpr unsigned READ  = 0;
  static constexpr unsigned WRITE = 1;
  static constexpr unsigned LOW   = 0;
  static constexpr unsigned HI    = 1;

  static constexpr uint8_t ADS_RANGE_6V   = 0x0;
  static constexpr uint8_t ADS_RANGE_4V   = 0x1;
  static constexpr uint8_t ADS_RANGE_2V   = 0x2;
  static constexpr uint8_t ADS_RANGE_1V   = 0x3;
  static constexpr uint8_t ADS_RANGE_p5V  = 0x4;
  static constexpr uint8_t ADS_RANGE_p25V = 0x5;

  static constexpr uint8_t ADS_RATE_8SPS   = 0x0;
  static constexpr uint8_t ADS_RATE_16SPS  = 0x1;
  static constexpr uint8_t ADS_RATE_32SPS  = 0x2;
  static constexpr uint8_t ADS_RATE_64SPS  = 0x3;
  static constexpr uint8_t ADS_RATE_128SPS = 0x4;
  static constexpr uint8_t ADS_RATE_250SPS = 0x5;
  static constexpr uint8_t ADS_RATE_475SPS = 0x6;
  static constexpr uint8_t ADS_RATE_860SPS = 0x7;

private:
  static int  InitGPIOPin( const int pin, const unsigned direction );
  static void CloseGPIO( const int pin );
  static int  GPIORead( const int fd );
  static void GPIOWrite( const int fd, const unsigned val );

  static void InitPWM();
  static void ClosePWM();

  static constexpr int ads_default_address = 0x48;
  static int InitI2C();
  void       PushADCSetting();
  int16_t    ADCReadRaw();
  void       FlushLoop();
  void       InitI2CFlush();
  void       CloseI2CFlush();

  // High level function using i2C interface
  int gpio_trigger;
  int gpio_light;
  int gpio_adc;

  uint8_t adc_range;
  uint8_t adc_rate;
  uint8_t adc_channel;

  // I2C interface continuous streaming.
  bool i2c_flush;
  std::thread i2c_flush_thread;
  std::array<FixedQueue<float, 100>, 4> i2c_flush_array;
};

void
GPIO::Init()
{
  gpio_light   = InitGPIOPin(   light_pin, WRITE );
  gpio_trigger = InitGPIOPin( trigger_pin, WRITE );

  InitPWM();

  if( gpio_adc != -1 ){
    CloseI2CFlush();
  }

  gpio_adc = InitI2C();
  if( gpio_adc != -1 ){
    PushADCSetting();
    InitI2CFlush();
  }
}

GPIO::GPIO() :
  gpio_trigger( -1 ),
  gpio_light( -1 ),
  gpio_adc( -1 ),
  adc_range( ADS_RANGE_6V ),
  adc_rate( ADS_RATE_860SPS ),
  adc_channel( 0 )
{
}

GPIO::~GPIO()// Turning off LED light when the process has ended.
{
  if( gpio_light != -1 ){
    LightsOff();
    close( gpio_light );
    CloseGPIO( light_pin );
  }

  if( gpio_trigger != -1 ){
    close( gpio_trigger );
    CloseGPIO( trigger_pin );
  }

  ClosePWM();

  if( gpio_adc != -1 ){
    CloseI2CFlush();
    close( gpio_adc );
  }
}

// ******************************************************************************
// High level function for trigger control
// ******************************************************************************
void
GPIO::Pulse( const unsigned n, const unsigned wait ) const
{
  if( gpio_trigger == -1 ){
    throw std::runtime_error( "GPIO for trigger pin is not initialized" );
  }

  for( unsigned i = 0; i < n; ++i ){
    GPIOWrite( gpio_trigger, HI );
    usleep( 1 );
    GPIOWrite( gpio_trigger, LOW );
    usleep( wait );
  }
}

// ******************************************************************************
// High level function for light control
// ******************************************************************************
void
GPIO::LightsOn() const
{
  if( gpio_light == -1 ){
    throw std::runtime_error( "GPIO for light pin is not initialized" );
  }

  GPIOWrite( gpio_light, HI );
}

void
GPIO::LightsOff() const
{
  if( gpio_light == -1 ){
    throw std::runtime_error( "GPIO for light pin is not initialized" );
  }
  GPIOWrite( gpio_light, LOW );
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

  int fd;

  // Setting up the export
  fd = open( "/sys/class/gpio/export", O_WRONLY );
  if( -1 == fd ){
    sprintf( errmsg, "Failed to open /sys/class/gpio/export" );
    throw std::runtime_error( errmsg );
  }
  write_length = snprintf( buffer, buffer_length, "%u", pin );
  write( fd, buffer, write_length );
  close( fd );

  usleep( 1e5 );// Small pause to allow for

  // Setting direction.
  snprintf( path, buffer_length, "/sys/class/gpio/gpio%d/direction", pin );

  // Waiting for the sysfs to generated the corresponding file
  while( access( path, F_OK ) == -1 ){
    usleep( 1e5 );
  }

  fd = direction == READ ? open( path, O_WRONLY ) : open( path, O_WRONLY );
  if( -1 == fd ){
    sprintf( errmsg, "Failed to open gpio [%d] direction! [%s]", pin, path );
    throw std::runtime_error( errmsg );
  }

  int status = write( fd
                    , direction == READ ? "in" : "out"
                    , direction == READ ? 2    : 3 );
  if( status == -1 ){
    sprintf( errmsg, "Failed to set gpio [%d] direction!", pin );
    throw std::runtime_error( errmsg );
  }
  close( fd );

  // Opening GPIO PIN
  snprintf( path, buffer_length, "/sys/class/gpio/gpio%d/value", pin );
  fd = direction == READ ? open( path, O_RDONLY ) : open( path, O_WRONLY );
  if( -1 == fd ){
    sprintf( errmsg, "Failed to open gpio [%d] value! [%s]", pin, path );
    throw std::runtime_error( errmsg );
  }


  return fd;
}

int
GPIO::GPIORead( const int fd )
{
  char value_str[3];
  if( -1 == read( fd, value_str, 3 ) ){
    throw std::runtime_error( "Failed to read gpio value!" );
  }
  return atoi( value_str );
}

void
GPIO::GPIOWrite( const int fd, const unsigned val )
{
  if( 1 != write( fd, LOW == val ? "0" : "1", 1 ) ){
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
  if( -1 == fd ){
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
  if( -1 == fd ){
    sprintf( errmsg, "Failed to open /sys/class/pwm/pwmchip0/export" );
    throw std::runtime_error( errmsg );
  }
  write( fd, "0", 1 );
  write( fd, "1", 1 );

  // Waiting for the sysfs to generated the corresponding file
  while( access( "/sys/class/pwm/pwmchip0/pwm0/enable", F_OK ) == -1 ){
    usleep( 1e5 );
  }

  while( access( "/sys/class/pwm/pwmchip0/pwm1/enable", F_OK ) == -1 ){
    usleep( 1e5 );
  }

  close( fd );
}

void
GPIO::ClosePWM()
{
  char errmsg[1024];
  int fd = open( "/sys/class/pwm/pwmchip0/pwm1/enable", O_WRONLY );
  write( fd, "0", 1 );

  fd = open( "/sys/class/pwm/pwmchip0/pwm0/enable", O_WRONLY );
  write( fd, "0", 1 );

  fd = open( "/sys/class/pwm/pwmchip0/unexport", O_WRONLY );
  if( -1 == fd ){
    sprintf( errmsg, "Failed to open /sys/class/pwm/pwmchip0/unexport" );
    throw std::runtime_error( errmsg );
  }
  write( fd, "0", 1 );
  write( fd, "1", 1 );
  close( fd );
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

  char enable_path[1024];
  char duty_path[1024];
  char period_path[1024];
  char duty_str[10];
  char period_str[10];
  char errmsg[1024];

  sprintf( enable_path, "/sys/class/pwm/pwmchip0/pwm%u/enable",     channel );
  sprintf( duty_path,   "/sys/class/pwm/pwmchip0/pwm%u/duty_cycle", channel );
  sprintf( period_path, "/sys/class/pwm/pwmchip0/pwm%u/period",     channel );
  unsigned duty_len   = sprintf( duty_str,    "%u", duty );
  unsigned period_len = sprintf( period_str,  "%u", period );

  int fd_enable = open( enable_path, O_WRONLY );
  int fd_duty   = open( duty_path,   O_WRONLY );
  int fd_period = open( period_path, O_WRONLY );

  if( fd_enable == -1 || fd_duty == -1 || fd_period == -1 ){
    sprintf( errmsg, "Failed to open /sys/class/pwm/pwmchip%u settings", c );
    throw std::runtime_error( errmsg );
  }

  printf( "%s %s\n", period_str, duty_str );

  write( fd_enable, "0",        1 );
  write( fd_period, period_str, period_len  );
  write( fd_duty,   duty_str,   duty_len  );
  write( fd_enable, "1",        1 );

  close( fd_enable );
  close( fd_duty );
  close( fd_period );
}

// ******************************************************************************
// I2C related functions
// Main reference:http://www.bristolwatch.com/rpi/ads1115.html
// ******************************************************************************
float
GPIO::ReadADC( const unsigned channel )
{
  return i2c_flush_array[channel].back();
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
  if( fd  < 0 ){
    sprintf( errmsg, "Error: Couldn't open i2c device! %s", "/dev/i2c-1" );
    throw std::runtime_error( errmsg );
  }

  // connect to ADS1115 as i2c slave
  if( ioctl( fd, I2C_SLAVE, 0x48 ) < 0 ){
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

  usleep( 1e5 );

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


float GPIO::ReadNTCTemp( const unsigned channel )
{
  // Standard values for NTC resistors used in circuit;
  static const float T_0 = 25 + 273.15;
  static const float R_0 = 10000;
  static const float B   = 3500;

  // Standard operation values for biasing circuit
  static const float V_total = 5000.00;
  static const float R_ref   = 10000;

  // Dynamic convertion
  const float v = ReadADC( channel );
  const float R = R_ref * v / ( V_total - v );

  // Temperature equation from Steinhart–Hart equation.
  // 1/T = 1/T0 + 1/B * ln(R/R0)
  return ( T_0 * B )/( B + T_0* std::log( R/R_0 ) ) - 273.15;
}

float GPIO::ReadRTDTemp( const unsigned channel )
{
  // Typical value of RTDs in circuit
  static const float R_0 = 10000;
  static const float T_0 = 273.15;
  static const float a   = 0.003850;

  // standard operation values for biasing circuit
  static const float V_total = 5000.00;
  static const float R_ref   = 10000;

  // Dynamic conversion
  const float v = ReadADC( channel );
  const float R = R_ref * v / ( V_total -v );

  // Temperature conversion is simply
  // R = R_0 (1 + a (T - T0))
  return T_0 + ( R - R_0 )/( R_0 * a ) - T_0;
}

void GPIO::FlushLoop()
{
  while( i2c_flush == true ){
    for( unsigned channel = 0; channel < 4; ++channel ){
      adc_channel = channel;
      PushADCSetting();

      const int16_t adc   = ADCReadRaw();
      const uint8_t range = adc_range& 0x7;
      const float conv    = range == ADS_RANGE_6V  ? 6144.0 / 32678.0 :
                            range == ADS_RANGE_4V  ? 4096.0 / 32678.0 :
                            range == ADS_RANGE_2V  ? 2048.0 / 32678.0 :
                            range == ADS_RANGE_1V  ? 1024.0 / 32678.0 :
                            range == ADS_RANGE_p5V ?  512.0 / 32678.0 :
                            256.0 / 32678.0;
      i2c_flush_array[channel].push( adc * conv );
      usleep( 1e5 );
    }
  }
}

void GPIO::InitI2CFlush()
{
  i2c_flush        = true;
  i2c_flush_thread = std::thread( [this] {
    this->FlushLoop();
  } );
}

void GPIO::CloseI2CFlush()
{
  i2c_flush = false;
  i2c_flush_thread.join();
}


// ******************************************************************************
// BOOST Python stuff
// ******************************************************************************
#ifndef STANDALONE
#include <boost/python.hpp>

BOOST_PYTHON_MODULE( gpio )
{
  auto gpio_class = boost::python::class_<GPIO, boost::noncopyable>( "GPIO" )
                    .def( "init",      &GPIO::Init        )
                    .def( "pulse",     &GPIO::Pulse       )
                    .def( "light_on",  &GPIO::LightsOn    )
                    .def( "light_off", &GPIO::LightsOff   )
                    .def( "pwm",       &GPIO::SetPWM      )
                    .def( "adc_read",  &GPIO::ReadADC     )
                    .def( "adc_range", &GPIO::SetADCRange )
                    .def( "adc_rate",  &GPIO::SetADCRate  )
                    .def( "rtd_read",  &GPIO::ReadRTDTemp )
                    .def( "ntc_read",  &GPIO::ReadNTCTemp )
  ;

  gpio_class.attr( "ADS_RANGE_6V" )    = GPIO::ADS_RANGE_6V;
  gpio_class.attr( "ADS_RANGE_4V" )    = GPIO::ADS_RANGE_4V;
  gpio_class.attr( "ADS_RANGE_2V" )    = GPIO::ADS_RANGE_2V;
  gpio_class.attr( "ADS_RANGE_1V" )    = GPIO::ADS_RANGE_1V;
  gpio_class.attr( "ADS_RANGE_p5V" )   = GPIO::ADS_RANGE_p5V;
  gpio_class.attr( "ADS_RANGE_p25V" )  = GPIO::ADS_RANGE_p25V;
  gpio_class.attr( "ADS_RATE_8SPS" )   = GPIO::ADS_RATE_8SPS;
  gpio_class.attr( "ADS_RATE_16SPS" )  = GPIO::ADS_RATE_16SPS;
  gpio_class.attr( "ADS_RATE_32SPS" )  = GPIO::ADS_RATE_32SPS;
  gpio_class.attr( "ADS_RATE_64SPS" )  = GPIO::ADS_RATE_64SPS;
  gpio_class.attr( "ADS_RATE_128SPS" ) = GPIO::ADS_RATE_128SPS;
  gpio_class.attr( "ADS_RATE_250SPS" ) = GPIO::ADS_RATE_250SPS;
  gpio_class.attr( "ADS_RATE_475SPS" ) = GPIO::ADS_RATE_475SPS;
  gpio_class.attr( "ADS_RATE_860SPS" ) = GPIO::ADS_RATE_860SPS;
}
#endif
