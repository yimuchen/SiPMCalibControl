#include "logger_private.hpp"
#include <boost/format.hpp>
#include <regex>

// ** Global object
logger Logger;

// Color coding functions
std::string
color( const std::string& str, const unsigned colorcode )
{
  const std::regex color_regex( "\033\\[[\\d;]+m" );
  const std::string ans = std::regex_replace( str, color_regex, "" );
  return ( boost::format( "\033[1;%dm%s\033[0m" ) % colorcode % ans ).str();
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


void
update( const std::string& a, const std::string& b )
{
  Logger.update( a, b );
}

void
clear_update()
{
  Logger.clear_update();
}

void
printmsg( const std::string& x )
{
  Logger.printmsg( x );
}

void
printwarn( const std::string& x )
{
  Logger.printmsg( x, YELLOW( "[WARNING]" ) );
}

void
printerr( const std::string& x )
{
  Logger.printmsg( x, RED( "[ERROR]" ) );
}
