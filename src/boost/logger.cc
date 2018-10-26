#include "logger.hpp"
#include <boost/python.hpp>

BOOST_PYTHON_MODULE( logger )
{
  boost::python::def( "update",       &update       );
  boost::python::def( "clear_update", &clear_update );
  boost::python::def( "printmsg",     &printmsg     );
  boost::python::def( "printwarn",    &printwarn    );
  boost::python::def( "printerr",     &printerr     );
}
