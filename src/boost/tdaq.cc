#include <boost/python.hpp>
#include <tdaq.hpp>

BOOST_PYTHON_MODULE(tdaq)
{
  boost::python::def("measure_once", measure_once);
}