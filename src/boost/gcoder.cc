#include <boost/python.hpp>
#include <gcoder.hpp>

BOOST_PYTHON_MODULE( gcoder )
{
  boost::python::class_<GCoder>( "GCoder" )
  //.def( boost::python::init<const std::string&>() )
  .def( "init_printer",     &GCoder::init_printer )
  // Hiding functions from python
  //.def( "pass_gcode",       &GCoder::pass_gcode )
  .def( "get_settings",     &GCoder::get_settings )
  .def( "set_speed_limit",  &GCoder::set_speed_limit )
  .def( "move_to_position", &GCoder::move_to_position )
  .def_readonly( "dev_path", &GCoder::dev_path )
  .def_readonly( "opx",      &GCoder::opx )
  .def_readonly( "opy",      &GCoder::opy )
  .def_readonly( "opz",      &GCoder::opz );
}
