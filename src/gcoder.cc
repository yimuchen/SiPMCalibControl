#include "logger.hpp"

#include <chrono>
#include <cmath>
#include <stdexcept>
#include <string>

// Stuff required for tty input and output
#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

struct GCoder
{
  GCoder();
  // GCoder( const std::wstring& dev );
  ~GCoder();

  // Static data members
  static const float _max_x;
  static const float _max_y;
  static const float _max_z;

  static float
  max_x(){ return _max_x; }
  static float
  max_y(){ return _max_y; }
  static float
  max_z(){ return _max_z; }

  void InitPrinter( const std::string& dev );

  // Raw motion command setup
  std::string RunGcode(
    const std::string& gcode,
    const unsigned     attempt = 0,
    const unsigned     waitack = 1e4,
    const bool         verbose = false
    ) const;

  // Abstaction of actual GCode commands
  void SendHome();

  std::wstring GetSettings() const;

  void SetSpeedLimit(
    float x = std::nanf(""),
    float y = std::nanf(""),
    float z = std::nanf("")
    );

  void MoveTo(
    float      x       = std::nanf(""),
    float      y       = std::nanf(""),
    float      z       = std::nanf(""),
    const bool verbose = false
    );

  void MoveToRaw(
    float      x       = std::nanf(""),
    float      y       = std::nanf(""),
    float      z       = std::nanf(""),
    const bool verbose = false
    );

  // Floating point comparison.
  static bool MatchCoord( double x, double y );

public:
  int         printer_IO;
  float       opx, opy, opz; // current position of the printer
  float       vx, vy, vz; // Speed of the gantry head.
  std::string dev_path;
};


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
GCoder::InitPrinter( const std::string& dev )
{
  static const int speed = B115200;
  struct termios tty;
  char errormessage[2048];

  dev_path   = dev;
  printer_IO = open( dev.c_str(), O_RDWR | O_NOCTTY | O_SYNC );

  if( printer_IO < 0 ){
    sprintf( errormessage,
      "Failed to open printer IO [%d] %s", printer_IO, dev.c_str() );
    throw std::runtime_error( errormessage  );
  }

  if( tcgetattr( printer_IO, &tty ) < 0 ){
    sprintf( errormessage,
      "Error getting termios settings %s",  strerror( errno ) );
    throw std::runtime_error( errormessage );
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
    sprintf( errormessage, "Error setting termios: %s", strerror( errno ) );
    throw std::runtime_error( errormessage );
  }

  printmsg( GREEN( "[PRINTER]" ), "Waking up printer...." );
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
  char msg[1024];
  int readlen;
  std::string ackstr = "";
  bool awk           = false;

  // Pretty output
  std::string pstring = gcode;
  pstring[pstring.length()-1] = '\0';// Getting rid of trailing new line

  sprintf( msg, "[%s] to USBTERM[%d] (attempt %u)...",
    pstring.c_str(), printer_IO, attempt );

  if( printer_IO < 0 ){
    throw std::runtime_error( "Printer is not available for commands" );
  }

  if( attempt >= maxtry ){
    sprintf( msg,
      "ACK string was not received after [%d] attempts!"
      " The message could be dropped or there is something wrong with"
      " the printer!",  maxtry );
    throw std::runtime_error( msg );
  }

  // Sending output
  if( verbose ){ update( msghead, msg ); }
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
      sprintf( msg,
        "Error reading printer output: %s", strerror( errno ) );
      throw std::runtime_error( msg );
    }
  } while( !awk && duration_cast<microseconds>( t2-t1 ).count() < waitack );

  // Checking output
  if( awk ){
    if( verbose ){
      strcat( msg, "... Done!" );
      update( msghead, msg );
    }
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
  static const float maxv       = 300./14.;// Setting the maximum speed
  static const char gcode_fmt[] = "M203 X%.2f Y%.2f Z%.2f\n";
  char gcode[1024];

  // NAN detection.
  if( x != x ){ x = vx; }
  if( y != y ){ y = vy; }
  if( z != z ){ z = vz; }

  if( x > maxv ){ x = maxv; }
  if( y > maxv ){ y = maxv; }
  if( z > maxv ){ z = maxv; }

  sprintf( gcode, gcode_fmt, x, y, z );
  RunGcode( gcode, false );

  vx = x;
  vy = y;
  vz = z;
}

void
GCoder::MoveTo( float x, float y, float z, bool verbose )
{
  static constexpr float min_z_safety = 20;

  if( z < min_z_safety && opz < min_z_safety ){
    MoveToRaw( opx, opy, min_z_safety, verbose );
    MoveToRaw( x,   y,   min_z_safety, verbose  );
    MoveToRaw( x,   y,   z,            verbose );
  } else if( opz < min_z_safety ){
    MoveToRaw( opx, opy, min_z_safety, verbose );
    MoveToRaw( x,   y,   z,            verbose  );
  } else if( z < min_z_safety ){
    MoveToRaw( x, y, min_z_safety, verbose );
    MoveToRaw( x, y, z,            verbose );
  } else {
    MoveToRaw( x, y, z, verbose );
  }
}

void
GCoder::MoveToRaw( float x, float y, float z, bool verbose )
{
  static const std::string msghead = GREEN( "[GANTRYPOS]" );
  static const char move_fmt[]     = "G0 X%.1f Y%.1f Z%.1f\n";

  char gcode[128];
  char msg[1024];
  float temp;
  int check;

  // Setting up target position
  opx = x == x ? x : opx;
  opy = y == y ? y : opy;
  opz = z == z ? z : opz;

  // Rounding to closest 0.1 (precision of gantry system)
  opx = std::round( opx * 10 ) / 10;
  opy = std::round( opy * 10 ) / 10;
  opz = std::round( opz * 10 ) / 10;

  // checking for boundary
  if( opx < 0 || opx > max_x() ||
      opy < 0 || opy > max_y() ||
      opz < 0 || opz > max_z() ){
    printwarn( "Coordinates is outside of gantry limit! Moving the "
      "destination back into reasonable limits." );
    opx = std::max( std::min( opx, max_x() ), 0.0f );
    opy = std::max( std::min( opy, max_y() ), 0.0f );
    opz = std::max( std::min( opz, max_z() ), 0.0f );
  }

  // Running the code
  sprintf( gcode, move_fmt, opx, opy, opz );
  RunGcode( gcode, 0, 100, verbose );
  if( verbose ){ clear_update(); }

  do {
    // Getting current position command
    usleep( 5e4 );
    const std::string checkmsg = RunGcode( "M114\n", 0, 100, verbose );

    check = sscanf( checkmsg.c_str(),
      "X:%f Y:%f Z:%f E:%f Count X:%f Y:%f Z:%f",
      &opx, &opy, &opz, &temp, &x, &y, &z );

    if( check == 7 ){
      sprintf( msg,
        "Target (%.1lf %.1lf %.1lf), Current (%.1lf, %.1lf, %.1lf)...",
        opx, opy, opz, x, y, z );

      if( verbose ){ update( msghead, msg ); }

      if( MatchCoord( opx, x ) &&
          MatchCoord( opy, y ) &&
          MatchCoord( opz, z ) ){
        if( verbose ){
          strcat( msg, " Done!" );
          update( msghead, msg );
        }
        break;
      }

    } else {
      if( verbose ){
        std::string pmsg = checkmsg;

        for( unsigned i = 0; i < pmsg.length(); ++i ){
          if( pmsg[i] == '\n' ){ pmsg[i] = '\\'; }
        }

        if( pmsg.length() > 54 ){
          pmsg.resize( 54 );
          pmsg += "...";
        }
        // flush_update();
        // sprintf( msg, "Couldn't parse string [%s]! Trying again!\n\n",
        //   pmsg.c_str() );
        // printwarn( msg );
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


const float GCoder::_max_x = 345;
const float GCoder::_max_y = 450;
const float GCoder::_max_z = 460;


#ifndef STANDALONE
#include <boost/python.hpp>

BOOST_PYTHON_MODULE( gcoder )
{
  boost::python::class_<GCoder>( "GCoder" )
  // .def( boost::python::init<const std::string&>() )
  .def( "initprinter",     &GCoder::InitPrinter )
  // Hiding functions from python
  // .def( "pass_gcode",       &GCoder::pass_gcode )
  .def( "getsettings",     &GCoder::GetSettings )
  .def( "set_speed_limit", &GCoder::SetSpeedLimit )
  .def( "moveto",          &GCoder::MoveTo )
  .def( "sendhome",        &GCoder::SendHome )
  .def_readonly( "dev_path", &GCoder::dev_path )
  .def_readonly( "opx",      &GCoder::opx )
  .def_readonly( "opy",      &GCoder::opy )
  .def_readonly( "opz",      &GCoder::opz )
  // Static methods
  .def( "max_x", &GCoder::max_x )
  .staticmethod( "max_x" )
  .def( "max_y", &GCoder::max_y )
  .staticmethod( "max_y" )
  .def( "max_z", &GCoder::max_z )
  .staticmethod( "max_z" )
  ;
}
#endif