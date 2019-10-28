// Using examples of wiring PI
// https://elinux.org/RPi_GPIO_Code_Samples#WiringPi
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include <stdexcept>

class GPIO
{
public:
  GPIO();
  ~GPIO();

  void Init();
  void Pulse( const unsigned n, const unsigned wait ) const;
  void LightsOn() const;
  void LightsOff() const;

  int gpio_trigger;
  int gpio_pwd;
  int gpio_light;

  // On the raspberry PI, these pins correspond to the BCM pin from
  // wiringPi's `gpio readall` command
  static constexpr unsigned trigger_pin = 21;
  static constexpr unsigned pwd_pin     = 0;
  static constexpr unsigned light_pin   = 26;

  static constexpr unsigned READ  = 0;
  static constexpr unsigned WRITE = 1;
  static constexpr unsigned LOW   = 0;
  static constexpr unsigned HI    = 1;

private:
  static int  InitGPIOPin( const int pin, const unsigned direction );
  static void CloseGPIO( const int pin );
  static int  GPIORead( const int fd );
  static void GPIOWrite( const int fd, const unsigned val );
};

void
GPIO::Init()
{
  gpio_light   = InitGPIOPin(   light_pin, WRITE );
  gpio_trigger = InitGPIOPin( trigger_pin, WRITE );
}

GPIO::GPIO() :
  gpio_trigger( -1 ),
  gpio_pwd( -1 ),
  gpio_light( -1 )
{
}

GPIO::~GPIO()// Turning off LED light when the process has ended.
{
  LightsOff();

  close( gpio_trigger );
  close( gpio_light );
  CloseGPIO( trigger_pin );
  CloseGPIO( light_pin );
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
  char buffer [buffer_length];
  int fd = open( "/sys/class/gpio/unexport", O_WRONLY );
  if( -1 == fd ){
    throw std::runtime_error( "Failed to open un-export for writing!" );
  }

  write_length = snprintf( buffer, buffer_length, "%d", pin );
  write( fd, buffer, write_length );

  close( fd );
}


// ******************************************************************************
// BOOST Python stuff
// ******************************************************************************
#ifndef STANDALONE
#include <boost/python.hpp>

BOOST_PYTHON_MODULE( gpio )
{
  boost::python::class_<GPIO, boost::noncopyable>( "GPIO" )
  .def( "init",      &GPIO::Init   )
  .def( "pulse",     &GPIO::Pulse  )
  .def( "light_on",  &GPIO::LightsOn  )
  .def( "light_off", &GPIO::LightsOff  )
  ;
}
#endif
