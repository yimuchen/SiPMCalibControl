#include "logger.hpp"

#include <cstdio>
#include <map>

/**
 * @brief Private class for handling the logging outputs output
 * @ingroup Logger
 *
 * Static single instance global class for handling the output loggings. Raw
 * escape ASCII code is used to handle vertical navigation of the output string.
 *
 * The update function functions is handled by a map of header string to the
 *line
 * strings. Each time an update is requested, first the screen is scrubbed of
 *the
 * stored contents based on the length of the of the stored string, the
 *internals
 * map is updated, then for each line stored in the map, a new string is printed
 * onto the terminal. Notice this means that if the used mixes Update calls and
 * Print calls, the output may become mangled, and there probably isn't a easy
 * way to get around this.
 */
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
  void                               screenclear_update();
  void                               screenflush_update();
  void                               screenprint_update();
  FILE*                              outputptr;
};

static Logger GlobalLogger;// global object

static inline std::string
color( const std::string& str, const unsigned colorcode )
{
  char ans[1024];
  sprintf( ans, "\033[1;%dm%s\033[0m", colorcode, str.c_str() );
  return ans;
}


/**
 * @brief Making the string green when printed in the terminal
 */
std::string
GREEN( const std::string& str )
{ return color( str, 32 ); }

/**
 * @brief Making the string yellow when printed in the terminal
 */
std::string
YELLOW( const std::string& str )
{ return color( str, 33 );}

/**
 * @brief Making the string red when printed in the terminal
 */
std::string
RED( const std::string& str )
{ return color( str, 31 ); }

/**
 * @brief Making the string cyan when printed in the terminal
 */
std::string
CYAN( const std::string& str )
{ return color( str, 36 ); }


/**
 * @brief Printing and updated line on the specified header identifier.
 */
void
update( const std::string& a, const std::string& b )
{
  GlobalLogger.Update( a, b );
}


/**
 * @brief Clearing all lines associated with updates.
 */
void
clear_update()
{
  GlobalLogger.ClearUpdate();
}


/**
 * @brief Forcing all update string to be printed on screen now.
 */
void
flush_update()
{
  GlobalLogger.FlushUpdate();
}


/**
 * @brief Printing a message on screen with a standard header. This is
 * implemeneted as a parallel to the update method.
 */
void
printmsg( const std::string& header, const std::string& x )
{
  GlobalLogger.PrintMessage( x, header );
}


/**
 * @brief Printing a message on screen. Notice that a new line will
 *automatically
 * be added at the end of the string..
 */
void
printmsg( const std::string& x )
{
  GlobalLogger.PrintMessage( x );
}


/**
 * @brief Printing a message on screen with the standard yellow `[WARNING]`
 *string at the start of the line.
 */
void
printwarn( const std::string& x )
{
  GlobalLogger.PrintMessage( x, YELLOW( "[WARNING]" ) );
}


/**
 * @brief Printing a message on screen with the standard red `[ERROR]` string
 * at the start of the line.
 */
void
printerr( const std::string& x )
{
  GlobalLogger.PrintMessage( x, RED( "[ERROR]" ) );
}


/**
 * @brief Setting the logging output to some specific file descriptor.
 *
 * Notice this is not the FILE*, but the integer file descriptor used by the
 * operating system. This allows for non-standard files, such the stdout and
 * stderr, or other pseudo-file outputs to be used.
 */
void
setloggingdescriptor( const int fd )
{
  GlobalLogger.SetOutputDescriptor( fd );
}


/**
 * @brief Initialize to have output go to STDOUT.
 */
Logger::Logger()
{
  outputptr = stdout;
}


/**
 * @brief Attempt to close the descriptor.
 */
Logger::~Logger()
{
  fclose( outputptr );
}


/**
 * @brief Main function to call for update-like screen logging
 */
void
Logger::Update( const std::string& key, const std::string& msg )
{
  screenclear_update();
  _update[key] = msg;
  screenprint_update();
}


/**
 * @brief Main function to call for one-shot screen logging, new line is
 * automatically added.
 */
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


/**
 * @brief Forcing update to be printed again.
 */
void
Logger::FlushUpdate()
{
  Logger::screenprint_update();
}


/**
 * @brief Clearing the update outputs and clearing the internal storage.
 */
void
Logger::ClearUpdate()
{
  screenclear_update();
  _update.clear();
}


/**
 * @brief Clearing the screen of string stroed in update map.
 *
 * Vertical navigation is done via special escape string. String wiping is done
 * by printing white space over the existing output.
 */
void
Logger::screenclear_update()
{
  static const char prevline[]      = "\033[A";
  char              clearline[1024] = {0};

  for( auto it = _update.rbegin(); it != _update.rend(); ++it ){
    const auto&    p            = *it;
    const unsigned total_length = p.first.length()+p.second.length()+1;

    for( unsigned i = 0; i < total_length; ++i ){
      clearline[i] = ' ';
    }

    clearline[total_length] = '\0';//
    fprintf( outputptr, "%s\r%s\r", prevline, clearline );
    fflush( outputptr );
  }
}


/**
 * @brief Printing the current update cache onto the screen
 */
void
Logger::screenprint_update()
{
  for( const auto& p : _update ){
    fprintf( outputptr, "%s %s\n", p.first.c_str(), p.second.c_str() );
    fflush( outputptr );
  }
}


/**
 * @brief Changing the file descriptor to write to.
 *
 * Notice that we cannot close the file descriptor, as not all file descriptors
 * can be closed. This will have to be handled by the external FILE* pointer
 * (C++) or file object (python).
 */
void
Logger::SetOutputDescriptor( const int fd )
{
  if( fd == stdout->_fileno ){
    outputptr = stdout;
  } else if( fd == stderr->_fileno ){
    outputptr = stderr;
  } else {
    outputptr = fdopen( fd, "w" );// Open file descriptor to open mode
  }
}
