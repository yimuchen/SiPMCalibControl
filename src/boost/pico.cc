#include <boost/python.hpp>
#include "pico.hpp"

BOOST_PYTHON_MODULE( pico )
{
  boost::python::class_<PicoUnit, boost::noncopyable>( "PicoUnit" )
  .def( "settrigger",       &PicoUnit::SetTrigger )
  .def( "setblocknums",     &PicoUnit::SetBlockNums )
  .def( "startrapidblocks", &PicoUnit::StartRapidBlock )
  .def( "isready",          &PicoUnit::IsReady )
  .def( "waitready",        &PicoUnit::WaitTillReady )
  .def( "flushbuffer",      &PicoUnit::FlushToBuffer )
  .def( "printbuffer" ,     &PicoUnit::DumpBuffer )
  ;
}

