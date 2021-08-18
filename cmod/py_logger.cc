// PYTHON BINDINGS
#include "logger.hpp"
#include <pybind11/pybind11.h>

inline void
printmsg_noheader( const std::string& x )
{ return printmsg( x ); }

inline void
printmsg_header( const std::string& x, const std::string& y )
{ return printmsg( x, y ); }

PYBIND11_MODULE( logger, m )
{
  m.def( "GREEN",                  &GREEN  );
  m.def( "RED",                    &RED    );
  m.def( "YELLOW",                 &YELLOW );
  m.def( "CYAN",                   &CYAN   );

  m.def( "update",                 &update               );
  m.def( "clear_update",           &clear_update         );
  m.def( "flush_update",           &flush_update         );
  m.def( "printmsg",               &printmsg_header      );
  m.def( "printmsg",               &printmsg_noheader    );
  m.def( "printwarn",              &printwarn            );
  m.def( "printerr",               &printerr             );
  m.def( "set_logging_descriptor", &setloggingdescriptor );
  m.def( "set_rl_descriptor",      &set_rl_descriptors   );
}
