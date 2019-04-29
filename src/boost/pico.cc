#include "pico.hpp"
#include <boost/python.hpp>

BOOST_PYTHON_MODULE( pico )
{
  boost::python::class_<PicoUnit, boost::noncopyable>( "PicoUnit" )
  .def( "init",             &PicoUnit::Init            )
  .def( "settrigger",       &PicoUnit::SetTrigger      )
  .def( "setrange",         &PicoUnit::SetVoltageRange )
  .def( "setblocknums",     &PicoUnit::SetBlockNums    )
  .def( "startrapidblocks", &PicoUnit::StartRapidBlock )
  .def( "isready",          &PicoUnit::IsReady         )
  .def( "waitready",        &PicoUnit::WaitTillReady   )
  .def( "buffer",           &PicoUnit::GetBuffer       )
  .def( "flushbuffer",      &PicoUnit::FlushToBuffer   )
  .def( "dumpbuffer",       &PicoUnit::DumpBuffer      )
  .def( "printinfo",        &PicoUnit::PrintInfo       )
  .def( "adc2mv",           &PicoUnit::adc2mv          )
  // Defining data members as readonly:
  .def_readonly( "presamples",       &PicoUnit::presamples )
  .def_readonly( "postsamples",      &PicoUnit::postsamples )
  .def_readonly( "ncaptures",        &PicoUnit::ncaptures )
  .def_readonly( "timeinterval",     &PicoUnit::timeinterval )
  .def_readonly( "triggerchannel",   &PicoUnit::triggerchannel )
  .def_readonly( "triggerdirection", &PicoUnit::triggerdirection )
  .def_readonly( "triggerlevel",     &PicoUnit::triggerlevel )
  .def_readonly( "triggerdelay",     &PicoUnit::triggerdelay )
  .def_readonly( "triggerwait",      &PicoUnit::triggerwait )
  ;
}
