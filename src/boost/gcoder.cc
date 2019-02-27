#include <boost/python.hpp>
#include <gcoder.hpp>

BOOST_PYTHON_MODULE( gcoder )
{
  boost::python::class_<GCoder>( "GCoder" )
  //.def( boost::python::init<const std::string&>() )
  .def( "initprinter",     &GCoder::InitPrinter )
  // Hiding functions from python
  //.def( "pass_gcode",       &GCoder::pass_gcode )
  .def( "getsettings",    &GCoder::GetSettings )
  .def( "set_speed_limit",  &GCoder::SetSpeedLimit )
  .def( "moveto",         &GCoder::MoveTo )
  .def_readonly( "dev_path", &GCoder::dev_path )
  .def_readonly( "opx",      &GCoder::opx )
  .def_readonly( "opy",      &GCoder::opy )
  .def_readonly( "opz",      &GCoder::opz );
}
