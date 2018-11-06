#include <boost/python.hpp>
#include <visual.hpp>

BOOST_PYTHON_MODULE( visual )
{
  boost::python::class_<Visual>( "Visual" )
    .def( "find_chip", &Visual::find_chip )
    .def( "scan_focus", &Visual::scan_focus )
    ;
}

