#include <boost/python.hpp>
#include <visual.hpp>

BOOST_PYTHON_MODULE( visual )
{
  boost::python::class_<Visual>( "Visual" )
    .def( "init_dev", &Visual::init_dev )
    .def( "find_chip", &Visual::find_chip )
    .def( "scan_focus", &Visual::scan_focus )
    .def_readonly( "dev_path", &Visual::dev_path )
    ;
}

