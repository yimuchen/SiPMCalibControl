#include <boost/python.hpp>
#include <visual.hpp>

BOOST_PYTHON_MODULE( visual )
{
  boost::python::class_<Visual>( "Visual" )
    .def( "init_dev", &Visual::init_dev )
    .def( "find_chip", &Visual::find_chip )
    .def( "sharpness", &Visual::sharpness )
    .def( "save_frame", &Visual::save_frame )
    .def( "frame_width", &Visual::frame_width )
    .def( "frame_height", &Visual::frame_height )
    .def_readonly( "dev_path", &Visual::dev_path )
    ;
  // Required for coordinate caluclation
  boost::python::class_<std::pair<double, double> >("DoublePair")
    .def_readwrite("first", &std::pair<double, double>::first)
    .def_readwrite("second", &std::pair<double, double>::second)
    .def_readwrite("x", &std::pair<double, double>::first)
    .def_readwrite("y", &std::pair<double, double>::second);
}

