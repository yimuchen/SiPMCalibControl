#include "gcoder.hpp"
#include <boost/algorithm/string.hpp>
#include <boost/format.hpp>
#include <cmath>
#include <iostream>
#include <chrono>

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

std::wstring
GCoder::get_printer_out()
{
  static const unsigned buffersize = 256;
  char buffer[buffersize];
  int rdlen;

  rdlen = read( printer_IO, buffer, sizeof( buffer ) - 1 );
  if( rdlen > 0 ){
    buffer[rdlen] = 1;
  } else if( rdlen < 0 ){
    throw std::runtime_error(
      ( boost::format( "Error reading printer output: %s" )
        % strerror( errno ) ).str()
      );
  }

  // Char array to wstring conversion.
  std::vector<char> v( buffer, buffer+rdlen );
  std::string str( v.begin(), v.end() );
  std::wstring ans( str.begin(), str.end() );

  return ans;
}

void
GCoder::send_home()
{
  pass_gcode( "G28\n" );
  opx = opy = opz = 0;
}

void
GCoder::pass_gcode(
  const std::string& gcode,
  const unsigned     wait,
  const unsigned     maxtry )
{
  using namespace std::chrono;
  boost::format printfmt(
      "Passing code [%s] to usb terminal [%s] (attempt %u) ");
  std::wstring awkstr ;
  std::string pstring = gcode;
  bool  awk = false;

  boost::trim_right( pstring );

  for( unsigned i = 0; i < maxtry && !awk ; ++i ){
    std::cout << printfmt % pstring % printer_IO % i << std::endl;

    write( printer_IO, gcode.c_str(), gcode.length() );
    tcdrain( printer_IO );

    high_resolution_clock::time_point t1 = high_resolution_clock::now();
    high_resolution_clock::time_point t2 = high_resolution_clock::now();
    do{
      awkstr = get_printer_out();
      if( awkstr.find(L"ok") ) { awk = true; }
    } while ( !awk && duration_cast<microseconds>(t2-t1).count() < wait );
  }

  if(!awk){
    std::cout << "Warning! AWK string was not received after ["
              << maxtry << "] attempts!"
              << " The message could be dropped or there is something could "
              << "be wrong with the printer!";
  }
}

void
GCoder::set_speed_limit( float x, float y, float z )
{
  static const float maxv = 300./14.;// Setting the maximum speed
  boost::format gcode_fmt( "M203 X%f Y%f Z%f\n" );
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
  double wait_time = 0;
  boost::format gcode_fmt( "G0 %s%.2f\n" );
  std::string gcode;

  // Velocity on the gantry isn't linear!
  // Moving x,y,z separately.
  if( x == x ){// NAN Checking!
    gcode     = ( gcode_fmt % "X" % x ).str();
    wait_time = fabs( x-opx ) / vx;
    pass_gcode( gcode );
    usleep( wait_time * 1e6 * 1.2 );
    opx = x;
  }
  if( y == y ){// NAN Checking!
    gcode     = ( gcode_fmt % "Y" % y ).str();
    wait_time = fabs( y-opy ) / vy;
    pass_gcode( gcode );
    usleep( wait_time * 1e6 * 1.2 );
    opy = y;
  }
  if( z == z ){// NAN Checking!
    gcode     = ( gcode_fmt % "Z" % z ).str();
    wait_time = fabs( z-opz ) / vz;
    pass_gcode( gcode );
    usleep( wait_time * 1e6 * 1.2 );
    opz = z;
  }
  return;
}
