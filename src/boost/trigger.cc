#include <boost/python.hpp>
#include <trigger.hpp>

BOOST_PYTHON_MODULE( trigger )
{
  boost::python::class_<trigger>( "trigger" )
  .def( "pulse", &trigger::pulse )
  .def( "init",  &trigger::init)
  ;
}

