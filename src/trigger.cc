// Using examples of wiring PI
// https://elinux.org/RPi_GPIO_Code_Samples#WiringPi

#include <stdexcept>

#include "logger.hpp"

#ifdef __arm__
#include <wiringPi.h>
#else
#include <unistd.h>// For sleep function
#endif

// Get this number by running `gpio readall` And find the corresponding value
/*
 +-----+-----+---------+------+---+---Pi 3B+-+---+------+---------+-----+-----+
 | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
 +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
 |     |     |    3.3v |      |   |  1 || 2  |   |      | 5v      |     |     |
 |   2 |   8 |   SDA.1 | ALT0 | 1 |  3 || 4  |   |      | 5v      |     |     |
 |   3 |   9 |   SCL.1 | ALT0 | 1 |  5 || 6  |   |      | 0v      |     |     |
 |   4 |   7 | GPIO. 7 |   IN | 0 |  7 || 8  | 0 | IN   | TxD     | 15  | 14  |
 |     |     |      0v |      |   |  9 || 10 | 1 | IN   | RxD     | 16  | 15  |
 |  17 |   0 | GPIO. 0 |   IN | 0 | 11 || 12 | 0 | IN   | GPIO. 1 | 1   | 18  |
 |  27 |   2 | GPIO. 2 |   IN | 0 | 13 || 14 |   |      | 0v      |     |     |
 |  22 |   3 | GPIO. 3 |   IN | 0 | 15 || 16 | 0 | IN   | GPIO. 4 | 4   | 23  |
 |     |     |    3.3v |      |   | 17 || 18 | 0 | IN   | GPIO. 5 | 5   | 24  |
 |  10 |  12 |    MOSI |   IN | 0 | 19 || 20 |   |      | 0v      |     |     |
 |   9 |  13 |    MISO |   IN | 0 | 21 || 22 | 0 | IN   | GPIO. 6 | 6   | 25  |
 |  11 |  14 |    SCLK |   IN | 0 | 23 || 24 | 1 | IN   | CE0     | 10  | 8   |
 |     |     |      0v |      |   | 25 || 26 | 1 | IN   | CE1     | 11  | 7   |
 |   0 |  30 |   SDA.0 |   IN | 1 | 27 || 28 | 1 | IN   | SCL.0   | 31  | 1   |
 |   5 |  21 | GPIO.21 |   IN | 1 | 29 || 30 |   |      | 0v      |     |     |
 |   6 |  22 | GPIO.22 |   IN | 1 | 31 || 32 | 0 | IN   | GPIO.26 | 26  | 12  |
 |  13 |  23 | GPIO.23 |   IN | 0 | 33 || 34 |   |      | 0v      |     |     |
 |  19 |  24 | GPIO.24 |   IN | 0 | 35 || 36 | 0 | IN   | GPIO.27 | 27  | 16  |
 |  26 |  25 | GPIO.25 |   IN | 0 | 37 || 38 | 0 | IN   | GPIO.28 | 28  | 20  |
 |     |     |      0v |      |   | 39 || 40 | 0 | IN   | GPIO.29 | 29  | 21  |
 +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
 | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
 +-----+-----+---------+------+---+---Pi 3B+-+---+------+---------+-----+-----+
 */
#define TRIGGER_PIN 29
#define LIGHT_PIN   25

class Trigger
{
public:
  Trigger();
  ~Trigger();

  void Init();
  void Pulse( const unsigned n, const unsigned wait ) const;
  void LightsOn() const;
  void LightsOff() const;

  int status;
};

Trigger::Trigger() : status( -1 ){}

Trigger::~Trigger() // Turning off LED light when the process has ended.
{
#ifdef __arm__
  if( status != -1 ){
    digitalWrite( LIGHT_PIN, 0 );
  }
#endif
}

void
Trigger::Init()
{
#ifdef __arm__
  status = wiringPiSetup();
#endif
  if( status == -1 ){
    throw std::runtime_error( "Wiring pi initialization failed" );
  }

#ifdef __arm__
  pinMode( TRIGGER_PIN, OUTPUT );
  pinMode( LIGHT_PIN,   OUTPUT );
#endif
}

void
Trigger::Pulse( const unsigned n, const unsigned wait ) const
{
  if( status == -1 ){
    throw std::runtime_error( "Wiring PI is not initialized" );
  }

  for( unsigned i = 0; i < n; ++i ){
#ifdef __arm__
    digitalWrite( TRIGGER_PIN, 1 );// On
    delayMicroseconds( 1 );
    digitalWrite( TRIGGER_PIN, 0 );// Off
    if( n > 1 ){
      delayMicroseconds( wait );
    }
#else
    usleep( wait );
#endif
  }
}

void
Trigger::LightsOn() const
{
  if( status == -1 ){
    throw std::runtime_error( "Wiring PI is not initialized" );
  }

#ifdef __arm__
  digitalWrite( LIGHT_PIN, 1 );
#endif
}

void
Trigger::LightsOff() const
{
  if( status == -1 ){
    throw std::runtime_error( "Wiring PI is not initialized" );
  }

#ifdef __arm__
  digitalWrite( LIGHT_PIN, 0 );
#endif
}

/** BOOST PYTHON STUFF */

#include <boost/python.hpp>

BOOST_PYTHON_MODULE( trigger )
{
  boost::python::class_<Trigger, boost::noncopyable>( "Trigger" )
  .def( "init",      &Trigger::Init   )
  .def( "pulse",     &Trigger::Pulse  )
  .def( "light_on",  &Trigger::LightsOn  )
  .def( "light_off", &Trigger::LightsOff  )

  // Defining data members as readonly:
  .def_readonly( "status", &Trigger::status  )
  ;
}
