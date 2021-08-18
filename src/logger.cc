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

  void SetOutputDescriptor( const int fd );

private:
  std::map<std::string, std::string> _update;
  void screenclear_update();
  void screenflush_update();
  void screenprint_update();
  FILE* outputptr;
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

void
setloggingdescriptor( const int fd )
{
  GlobalLogger.SetOutputDescriptor( fd );
}

/// Implementation of Logger class
Logger::Logger()
{
  // By default setup the logger such that it outputs to STDOUT
  outputptr = stdout;
}
Logger::~Logger()
{
  fclose( outputptr );
}

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
  // screenclear_update();
  if( header != "" ){
    fprintf( outputptr, "%s ", header.c_str() );
  }
  fprintf( outputptr, "%s\n", msg.c_str() );
  fflush( outputptr );
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
    const auto& p               = *it;
    const unsigned total_length = p.first.length() + p.second.length() + 1;

    for( unsigned i = 0; i < total_length; ++i ){
      clearline[i] = ' ';
    }

    clearline[total_length] = '\0';//
    fprintf( outputptr, "%s\r%s\r", prevline, clearline );
    fflush( outputptr );
  }
}

void
Logger::screenprint_update()
{
  for( auto it = _update.begin(); it != _update.end(); ++it ){
    fprintf( outputptr, "%s %s\n", it->first.c_str(), it->second.c_str() );
    fflush( outputptr );
  }
}

void
Logger::SetOutputDescriptor( const int fd )
{
  /// We will not be closing the file associated with the file descriptor!
  // The file object will have to be handled by external FILE* pointer that is
  // used to obtain the file descriptor

  if( fd == stdout->_fileno ){
    outputptr = stdout;
  } else if( fd == stderr->_fileno ){
    outputptr = stderr;
  } else {
    outputptr = fdopen( fd, "w" );// Open file descriptor to open mode
  }
}

#include <readline/readline.h>

void
set_rl_descriptors( const int in_fd, const int out_fd )
{
  if( in_fd == stdin->_fileno ){
    rl_instream = stdin;
  } else {
    rl_instream = fdopen( in_fd, "r" );
  }

  if( out_fd == stdout->_fileno ){
    rl_outstream = stdout;
  } else {
    rl_outstream = fdopen( out_fd, "w" );
  }
}
