#include "logger.hpp"

#include <cstdio>
#include <map>

class Logger
{
public:
  Logger();
  ~Logger();

  void Update( const std::string&, const std::string& );
  void PrintMessage( const std::string&, const std::string& = "" );
  void ClearUpdate();
  void FlushUpdate();

private:
  std::map<std::string, std::string> _update;
  void screenclear_update();
  void screenflush_update();
  void screenprint_update();
};

// ** Global object
Logger GlobalLogger;

// Color coding functions
std::string
color( const std::string& str, const unsigned colorcode )
{
  char ans[1024];
  // const std::regex color_regex( "\033\\[[\\d;]+m" );
  // const std::string ans = std::regex_replace( str, color_regex, "" );
  sprintf( ans, "\033[1;%dm%s\033[0m", colorcode, str.c_str() );
  return ans;
}

std::string
GREEN( const std::string& str )
{ return color( str, 32 ); }

std::string
YELLOW( const std::string& str )
{ return color( str, 33 );}

std::string
RED( const std::string& str )
{ return color( str, 31 ); }

std::string
CYAN( const std::string& str )
{ return color( str, 36 ); }


void
update( const std::string& a, const std::string& b )
{
  GlobalLogger.Update( a, b );
}

void
clear_update()
{
  GlobalLogger.ClearUpdate();
}

void
flush_update()
{
  GlobalLogger.FlushUpdate();
}

void
printmsg( const std::string& header, const std::string& x )
{
  GlobalLogger.PrintMessage( x, header );
}

void
printmsg( const std::string& x )
{
  GlobalLogger.PrintMessage( x );
}

void
printwarn( const std::string& x )
{
  GlobalLogger.PrintMessage( x, YELLOW( "[WARNING]" ) );
}

void
printerr( const std::string& x )
{
  GlobalLogger.PrintMessage( x, RED( "[ERROR]" ) );
}

/// Implementation of Logger class
Logger::Logger() {}
Logger::~Logger() {}

void
Logger::Update( const std::string& key, const std::string& msg )
{
  screenclear_update();
  _update[key] = msg;
  screenprint_update();
}

void
Logger::PrintMessage( const std::string& msg, const std::string& header )
{
  if( header != "" ){
    fprintf( stdout, "%s ", header.c_str() );
  }
  fprintf( stdout, "%s\n", msg.c_str() );
  fflush( stdout );
}

void
Logger::FlushUpdate()
{
  Logger::screenprint_update();
}


void
Logger::ClearUpdate()
{
  screenclear_update();
  _update.clear();
}

void
Logger::screenclear_update()
{
  static const char prevline[] = "\033[A";
  char clearline[1024]         = {0};

  for( auto it = _update.rbegin(); it != _update.rend(); ++it ){
    const auto& p = *it;
    const unsigned total_length = p.first.length() + p.second.length() + 1;

    for( unsigned i = 0; i < total_length; ++i ){
      clearline[i] = ' ';
    }

    clearline[total_length] = '\0';//
    fprintf( stdout, "%s\r%s\r", prevline, clearline );
    fflush( stdout );
  }
}

void
Logger::screenprint_update()
{
  for( auto it = _update.begin() ; it != _update.end() ; ++it ){
    fprintf( stdout, "%s %s\n", it->first.c_str(), it->second.c_str() );
    fflush( stdout );
  }
}

/******************************** BOOST PYTHON STUFF ***************************/

#include <boost/python.hpp>

inline void
printmsg_noheader( const std::string& x )
{ return printmsg( x ); }

inline void
printmsg_header( const std::string& x, const std::string& y )
{ return printmsg( x, y ); }

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
