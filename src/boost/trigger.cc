#include <boost/python.hpp>
#include <trigger.hpp>

BOOST_PYTHON_MODULE( trigger )
{
  boost::python::class_<Trigger>( "Trigger" )
  .def( "Pulse", &Trigger::Pulse )
  .def( "Init",  &Trigger::Init)
  ;
}

