#include "gcoder.hpp"
#include "logger.hpp"

#include <algorithm>
#include <boost/algorithm/string.hpp>
#include <boost/format.hpp>
#include <chrono>
#include <cmath>
#include <iostream>
#include <regex>

// Stuff required for tty input and output
#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

GCoder::GCoder() :
  printer_IO( -1 ),
  opx( -1 ),
  opy( -1 ),
  opz( -1 )
{};

GCoder::~GCoder()
{
  if( printer_IO > 0 ){
    close( printer_IO );
  }
}

void
GCoder::InitPrinter( const std::wstring& dev )
{
  static const int speed = B115200;
  struct termios tty;

  dev_path = dev;

  char dev_arr[2048];

  std::wcstombs( dev_arr, dev_path.c_str(), dev_path.length() );

  printer_IO = open( dev_arr, O_RDWR | O_NOCTTY | O_SYNC );
  if( printer_IO < 0 ){
    throw std::runtime_error( "Failed opening printer IO" );
  }

  if( tcgetattr( printer_IO, &tty ) < 0 ){
    throw std::runtime_error(
      ( boost::format( "Error getting termios settings: %s" )
        % strerror( errno ) ).str()
      );
  }

  cfsetospeed( &tty, (speed_t)speed );
  cfsetispeed( &tty, (speed_t)speed );

  tty.c_cflag |= ( CLOCAL | CREAD );// ignore modem controls
  tty.c_cflag &= ~CSIZE;
  tty.c_cflag |= CS8;// 8-bit characters
  tty.c_cflag &= ~PARENB;// no parity bit
  tty.c_cflag &= ~CSTOPB;// only need 1 stop bit
  tty.c_cflag &= ~CRTSCTS;// no hardware flowcontrol

  /* setup for non-canonical mode */
  tty.c_iflag &= ~( IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL | IXON );
  tty.c_lflag &= ~( ECHO | ECHONL | ICANON | ISIG | IEXTEN );
  tty.c_oflag &= ~OPOST;

  // fetch bytes as they become available
  tty.c_cc[VMIN]  = 1;
  tty.c_cc[VTIME] = 1;

  if( tcsetattr( printer_IO, TCSANOW, &tty ) != 0 ){
    throw std::runtime_error(
      ( boost::format( "Error setting termios: %s" )
        % strerror( errno ) ).str()
      );
  }

  printmsg( "Waking up printer...." );
  usleep( 5e6 );
  SendHome();

  return;
}

std::string
GCoder::RunGcode(
  const std::string& gcode,
  const unsigned     attempt,
  const unsigned     waitack,
  const bool         verbose ) const
{
  using namespace std::chrono;

  // static variables
  static const unsigned maxtry     = 1e2;
  static const unsigned buffersize = 65536;
  static const std::string msghead = GREEN( "[GCODE-SEND]" );

  // Readout data
  char buffer[buffersize];
  int readlen;
  std::string ackstr = "";
  bool awk           = false;

  // Pretty output
  boost::format printfmt( "[%s] to USBTERM[%s] (attempt %u)..." );
  std::string pstring = gcode;
  boost::trim_right( pstring );
  const std::string printmsg = ( printfmt%pstring%printer_IO%attempt ).str();

  if( printer_IO < 0 ){
    throw std::runtime_error( "Printer is not available for commands" );
  }

  if( attempt >= maxtry ){
    throw std::runtime_error(
      ( boost::format( "ACK string was not received after [%d] attempts!"
        " The message could be dropped or there is something wrong with"
        " the printer!" )% maxtry ).str() );
  }

  // Sending output
  if( verbose ){ update( msghead, printmsg ); }
  write( printer_IO, gcode.c_str(), gcode.length() );
  tcdrain( printer_IO );

  high_resolution_clock::time_point t1 = high_resolution_clock::now();
  high_resolution_clock::time_point t2 = high_resolution_clock::now();

  // Flushing output.
  do {
    readlen = read( printer_IO, buffer, sizeof( buffer ) - 1 );
    t2      = high_resolution_clock::now();

    if( readlen > 0 ){
      buffer[readlen] = 1;
      ackstr          = std::string( buffer, buffer+readlen );
      if( ackstr.find( "ok" ) != std::string::npos ){
        awk = true;
      }
    } else if( readlen < 0 ){
      throw std::runtime_error(
        ( boost::format( "Error reading printer output: %s" )
          % strerror( errno ) ).str()
        );
    }
  } while( !awk && duration_cast<microseconds>( t2-t1 ).count() < waitack );

  // Checking output
  if( awk ){
    if( verbose ){ update( msghead, printmsg+"...Done!" ); }
    return ackstr;
  } else {
    return RunGcode( gcode, attempt+1, waitack );
  }
}

void
GCoder::SendHome()
{
  RunGcode( "G28\n", 0, 4e9, true );
  clear_update();
  opx = opy = opz = 0;
}


std::wstring
GCoder::GetSettings() const
{
  std::string str = RunGcode( "M503\n" );
  return std::wstring( str.begin(), str.end() );
}

void
GCoder::SetSpeedLimit( float x, float y, float z )
{
  static const float maxv = 300./14.;// Setting the maximum speed
  boost::format gcode_fmt( "M203 X%.2f Y%.2f Z%.2f\n" );
  std::string gcode;

  // NAN detection.
  if( x != x ){ x = vx; }
  if( y != y ){ y = vy; }
  if( z != z ){ z = vz; }

  if( x > maxv ){ x = maxv; }
  if( y > maxv ){ y = maxv; }
  if( z > maxv ){ z = maxv; }

  gcode = ( gcode_fmt %  x % y % z ).str();

  RunGcode( gcode, false );

  vx = x;
  vy = y;
  vz = z;
}

void
GCoder::MoveTo( float x, float y, float z, bool verbose )
{
  // Check message of M114 is in:
  // "X:0.00 Y:0.00 Z:100.00 E:0.00 Count X: 0.00 Y:0.00 Z:126.01";
  static const std::string fltregex = "\\d+\\.\\d+";
  static const std::string wsregex  = "\\s*";
  static const std::regex checkfmt(
    ( boost::format(
      ".*X:(%1%) Y:(%1%) Z:(%1%).*"
      "Count.*X: (%1%) Y:(%1%) Z:(%1%)%2%.*"
      ) % fltregex % wsregex ).str()
    );
  static const std::string msghead = GREEN( "[GANTRYPOS]" );

  boost::format move_fmt( "G0 X%.1f Y%.1f Z%.1f\n" );
  std::string gcode;
  std::string checkmsg;
  std::smatch checkmatch;

  // Setting up target position
  opx = x == x ? x : opx;
  opy = y == y ? y : opy;
  opz = z == z ? z : opz;

  gcode = ( move_fmt % opx % opy % opz ).str();
  RunGcode( gcode, 0, 100, verbose );
  if( verbose ){ clear_update(); }

  do {
    // Getting current position command
    checkmsg = RunGcode( "M114\n", 0, 100, verbose );
    checkmsg.erase( std::remove( checkmsg.begin(), checkmsg.end(), '\n' ), checkmsg.end() );
    if( std::regex_match( checkmsg, checkmatch, checkfmt ) ){
      opx = std::stof( checkmatch[1].str() );
      opy = std::stof( checkmatch[2].str() );
      opz = std::stof( checkmatch[3].str() );
      x   = std::stof( checkmatch[4].str() );
      y   = std::stof( checkmatch[5].str() );
      z   = std::stof( checkmatch[6].str() );

      const std::string msg = ( boost::format(
        "Target (%.1lf %.1lf %.1lf), Current (%.1lf, %.1lf, %.1lf)..."
        ) % opx % opy % opz % x % y % z ).str();

      if( verbose ){ update( msghead, msg ); }

      if( MatchCoord( opx, x ) &&
          MatchCoord( opy, y ) &&
          MatchCoord( opz, z ) ){
        if( verbose ){ update( msghead, msg+"Done!" ); }
        break;
      }

    } else {
      if( verbose ){
        printwarn(
          ( boost::format( "Couldn't parse string [%s][%u]! Trying again!" )
            % checkmsg % checkmatch.size() ).str() );
      }
    }
  } while( 1 );

  return;
}

bool
GCoder::MatchCoord( double x, double y )
{
  // Rounding to closes 0.1
  x = std::round( x * 10 ) / 10;
  y = std::round( y * 10 ) / 10;
  return x == y;
}
