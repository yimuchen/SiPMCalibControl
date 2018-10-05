#include "gcode_stream.hpp"
#include <boost/format.hpp>
#include <boost/algorithm/string.hpp>
#include <cmath>
#include <iostream>

// Stuff required for tty input and output
#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

/**
 * @brief Global printer interface object to be initialized by python program
 */
int printerIO;


void
init_printer( const std::string& dev )
{
  static const int speed = B115200;
  struct termios tty;
  std::wstring awkstr;

  printerIO = open( dev.c_str(), O_RDWR | O_NOCTTY | O_SYNC );
  if( printerIO < 0 ){
    throw std::runtime_error( "Failed starting printer IO" );
  }

  if( tcgetattr( printerIO, &tty ) < 0 ){
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

  if( tcsetattr( printerIO, TCSANOW, &tty ) != 0 ){
    throw std::runtime_error(
      ( boost::format( "Error setting terminos: %s" )
        % strerror( errno ) ).str()
      );
  }

  std::cout << "Printer wake up in 5 seconds...." << std::endl;
  usleep( 5e6 );
  pass_gcode( "G28\n" );

  do {
    // Send to home in the x-y direction.
    awkstr = get_printer_out();
    // usleep(1e4);
  } while( awkstr.find( L"ok" ) == std::string::npos );

  return;
}


std::wstring
get_printer_out()
{
  static const unsigned buffersize = 256;
  char buffer[buffersize];
  int rdlen;

  rdlen = read( printerIO, buffer, sizeof( buffer ) - 1 );
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
pass_gcode( const std::string& gcode )
{
  std::string pstring = gcode;
  boost::trim_right( pstring );
  std::cout << boost::format( "Passing code [%s] to usb terminal [%s]" )
    % pstring // Stripping newline character
    % printerIO
            << std::endl;

  write( printerIO, gcode.c_str(), gcode.length() );
  tcdrain( printerIO );
}

void
move_to_position(
  float x,
  float y,
  float z
  )
{
  static const float xspeed = 300.0/13 ;
  static const float yspeed = 300.0/13 ;
  static const float zspeed = 100.0/22.0 ;
  std::string retstr;
  std::string gcode;

  if( x == x ){// NAN Checking!
    gcode = ( boost::format( "G0 X%f\n" ) % x ).str();
    pass_gcode( gcode );
    usleep( x / xspeed * 1e6 );
  }
  if( y == y ){// NAN Checking!
    gcode = ( boost::format( "G0 Y%f\n" ) % y ).str();
    pass_gcode( gcode );
    usleep( y / yspeed * 1e6 );
  }
  if( z == z ){// NAN Checking!
    gcode = ( boost::format( "G0 Z%f\n" ) % z ).str();
    pass_gcode( gcode );
    usleep( z / zspeed * 1e6 );
  }
}
