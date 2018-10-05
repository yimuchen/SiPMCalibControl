#include <boost/python.hpp>
#include <gcode_stream.hpp>

BOOST_PYTHON_MODULE(gcodestream)
{
  boost::python::def("init_printer",init_printer);
  boost::python::def("pass_gcode", pass_gcode);
  boost::python::def("move_to_position",move_to_position);
}