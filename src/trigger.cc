// Using examples of wiring PI
// https://elinux.org/RPi_GPIO_Code_Samples#WiringPi

#include <stdexcept>

#include "logger.hpp"

#ifdef __arm__
#include <wiringPi.h>
#else
#include <unistd.h> // For sleep function
#endif

// Get this number by running `gpio readall` And find the corresponding value
#define TRIGGER_PIN 29

class Trigger
{
public:
  Trigger();
  ~Trigger();

  void Init();
  void Pulse( const unsigned n, const unsigned wait ) const;

  int status;
};

Trigger::Trigger() : status(-1){}

Trigger::~Trigger(){}

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

/** BOOST PYTHON STUFF */

#include <boost/python.hpp>

BOOST_PYTHON_MODULE( trigger )
{
  boost::python::class_<Trigger, boost::noncopyable>( "Trigger" )
  .def( "init",  &Trigger::Init   )
  .def( "pulse", &Trigger::Pulse  )
  // Defining data members as readonly:
  .def_readonly( "status", &Trigger::status  )
  ;
}
