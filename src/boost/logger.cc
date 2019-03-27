#include "logger.hpp"
#include <boost/python.hpp>

inline void
printmsg_noheader( const std::string& x )
{ return printmsg( x ); }

inline void
printmsg_header( const std::string& x, const std::string& y )
{return printmsg( x, y ); }

BOOST_PYTHON_MODULE( logger )
{
  boost::python::def( "GREEN",        &GREEN  );
  boost::python::def( "RED",          &RED    );
  boost::python::def( "YELLOW",       &YELLOW );
  boost::python::def( "CYAN",         &CYAN   );

  boost::python::def( "update",       &update            );
  boost::python::def( "clear_update", &clear_update      );
  boost::python::def( "flush_update", &flush_update      );
  boost::python::def( "printmsg",     &printmsg_header   );
  boost::python::def( "printmsg",     &printmsg_noheader );
  boost::python::def( "printwarn",    &printwarn         );
  boost::python::def( "printerr",     &printerr          );
}
