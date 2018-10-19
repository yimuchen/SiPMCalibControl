#include "gcoder.hpp"
#include <boost/algorithm/string.hpp>
#include <boost/format.hpp>
#include <chrono>
#include <cmath>
#include <iostream>
#include <regex>
#include <algorithm>

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

GCoder::GCoder( const std::string& dev ) :
  printer_IO( -1 ),
  opx( -1 ),
  opy( -1 ),
  opz( -1 )
{
  init_printer( dev );
}

GCoder::~GCoder()
{
  if( printer_IO > 0 ){
    close( printer_IO );
  }
}

void
GCoder::init_printer( const std::string& dev )
{
  static const int speed = B115200;
  struct termios tty;
  std::wstring awkstr;

  dev_path = dev;

  printer_IO = open( dev_path.c_str(), O_RDWR | O_NOCTTY | O_SYNC );
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
      ( boost::format( "Error setting terminos: %s" )
        % strerror( errno ) ).str()
      );
  }

  std::cout << "Waking up printer...." << std::endl;
  usleep( 5e6 );
  // Send to home (with faster speed).
  send_home();
  // Resetting to slower speed for z
  set_speed_limit( 300, 300, 5 );

  return;
}

void
GCoder::send_home()
{
  pass_gcode( "G28\n", 0, 4e9 );
  opx = opy = opz = 0;
}

std::string
GCoder::pass_gcode(
  const std::string& gcode,
  const unsigned     attempt,
  const unsigned     waitack ) const
{
  using namespace std::chrono;

  // static variables
  static const unsigned maxtry     = 1e2;
  static const unsigned buffersize = 65536;

  // Readout data
  char buffer[buffersize];
  int readlen;
  std::string ackstr = "";
  bool awk           = false;

  // Pretty output
  boost::format printfmt(
    "\rPassing code [%s] to usb terminal [%s] (attempt %u) " );
  std::string pstring = gcode;
  boost::trim_right( pstring );

  if( attempt >= maxtry ){
    std::cout << "\nWarning! AWK string was not received after ["
              << maxtry << "] attempts!"
              << " The message could be dropped or there is something could "
              << "be wrong with the printer!";
    return "";
  }

  // Sending output
  std::cout << printfmt % pstring % printer_IO % attempt << std::flush;
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
      if( ackstr.find("ok")!= std::string::npos ){
        awk=true;
      }
    } else if( readlen < 0 ){
      throw std::runtime_error(
        ( boost::format( "Error reading printer output: %s" )
          % strerror( errno ) ).str()
        );
    }
  } while( !awk && duration_cast<microseconds>(t2-t1).count() < waitack );

  // Checking output
  if( awk ){
    std::cout << "...Done!" << std::endl;
    return ackstr;
  } else {
    return pass_gcode( gcode, attempt+1, waitack );
  }
}

std::wstring
GCoder::get_settings() const
{
  std::string str = pass_gcode( "M503\n" );

  return std::wstring( str.begin(), str.end() );
}

void
GCoder::set_speed_limit( float x, float y, float z )
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

  pass_gcode( gcode );

  vx = x;
  vy = y;
  vz = z;
}

void
GCoder::move_to_position( float x, float y, float z )
{
  // Check message of M114 is in:
  // "X:0.00 Y:0.00 Z:100.00 E:0.00 Count X: 0.00 Y:0.00 Z:126.01";
  static const std::string fltregex = "\\d+\\.\\d+";
  static const std::string wsregex  = "\\w*";
  static const std::regex checkfmt(
    ( boost::format(
      ".*X:.*(%1%).*Y:.*(%1%).*Z:.*(%1%).*X:.*(%1%).*Y:.*(%1%).*Z:.*(%1%).*"
      ) % fltregex  ).str()
    );

  boost::format move_fmt( "G0 X%.2f Y%.2f Z%.2f\n" );
  std::string gcode;
  std::string checkmsg;
  std::smatch checkmatch;

  // Setting up target position
  opx = x == x ? x : opx;
  opy = y == y ? y : opy;
  opz = z == z ? z : opz;

  gcode = ( move_fmt % opx % opy % opz ).str();
  pass_gcode( gcode );

  do {
    pass_gcode( "M114\n" );// Getting current position command
    checkmsg = pass_gcode( "M114\n" );
    checkmsg.erase(std::remove(checkmsg.begin(), checkmsg.end(), '\n'), checkmsg.end());
    if( std::regex_match( checkmsg, checkmatch, checkfmt ) ){
      opx = std::stof( checkmatch[1].str() );
      opy = std::stof( checkmatch[2].str() );
      opz = std::stof( checkmatch[3].str() );
      x   = std::stof( checkmatch[4].str() );
      y   = std::stof( checkmatch[5].str() );
      z   = std::stof( checkmatch[6].str() );
      if( opx == x && opy == y && opz == z ){
        break;
      } else {
        std::cout
          << boost::format( "Gantry in motion Target: [%f %f %f], current [%f %f %f]" )
          % opx % opy % opz % x % y % z
          << std::endl;
      }
    } else {
      std::cout << "Error parsing return string ["<< checkmsg
                << "]["<< checkmatch.size() << "]! Trying again!" << std::endl;
    }
  } while( 1 );

  return;
}
