#include <boost/python.hpp>
#include <trigger.hpp>

BOOST_PYTHON_MODULE( trigger )
{
  boost::python::class_<Trigger>( "Trigger" )
  .def( "pulse", &Trigger::Pulse )
  .def( "init",  &Trigger::Init)
  ;
}

