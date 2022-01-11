/**
 * @file gcoder.cc
 * @author Yi-Mu Chen
 * @brief Implementation of the GCode transfer interface.
 *
 * @class GCoder
 * @ingroup hardware
 * @brief Handling the transmission of gcode motion commands.
 *
 * @details Handling the transmission of gcode commands used for motion control
 * from raw gcode operations to user-ready, human-readable function with
 * appropriate abstraction of command sequences and additional signal parsing
 * between commands. The GCoder class is responsible for the transmission of
 * instructions to the 3D-printer for motion control. The transmission in
 * performed over USB using the UNIX termios interface. The full documentation
 * could be found [here][s-port].
 *
 * The class also abstracts motion controls which may or may not involve many
 * gcode commands into single functions with parameters which is simpler to call
 * for end users. For the full list of available marlin-flavored gcode, see
 * [here][marlin]. Due to how communications is handled in the kernel, not all
 * motions is abstractable in C++, with some needing to be handled at python
 * level. Those will be high-lighted for in the various code segments.
 *
 * [s-port]: https://www.xanthium.in/Serial-Port-Programming-on-Linux
 * [marlin]: https://marlinfw.org/meta/gcode/
 */
#include "gcoder.hpp"
#include "logger.hpp"

#include <chrono>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>

// Stuff required for tty input and output
#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <sys/file.h>
#include <termios.h>
#include <unistd.h>

/**
 * @brief Hard limit coordinates for gantry motion.
 * @details As there are now stop limiter for the gantry maximum motion range
 * value, here, progammatically add a hard input into the system to avoid
 * hardware damaged.
 * @{
 */
const float GCoder::_max_x = 345;
const float GCoder::_max_y = 200;
const float GCoder::_max_z = 460;

/** @} */

/**
 * @brief Forward declaration of static helper functions.
 */
static bool check_ack( const std::string& cmd, const std::string& msg );

/**
 * @brief Initializing the communications interface.
 *
 * Low level instructions in the termios interface for setting up the read
 * speed and mode for the communicating with the printer over USB. This part of
 * the code currently considered black-magicm as most of the statements are
 * copy from [here][s-port], so do not edit statements containing the tty
 * container unless you are absolutely sure about what you are doing.
 *
 * After initialization, the printer will always perform these 3 steps:
 * - Send the gantry back home and reset coordinates ot (0,0,0).
 * - Set the motion speed to something much faster
 * - Set the acceleration speed to 3 times the factory default.
 *
 * [s-port]: https://www.xanthium.in/Serial-Port-Programming-on-Linux
 */
void
GCoder::Init( const std::string& dev )
{
  static const int speed = B115200;

  struct termios tty;
  char           errormessage[2048];

  dev_path   = dev;
  printer_IO = open( dev.c_str(), O_RDWR | O_NOCTTY | O_NONBLOCK | O_ASYNC );

  if( printer_IO < 0 ){
    sprintf( errormessage,
             "Failed to open printer IO [%d] %s",
             printer_IO,
             dev.c_str() );
    throw std::runtime_error( errormessage  );
  }

  int lock = flock( printer_IO, LOCK_EX | LOCK_NB );
  if( lock ){
    close( printer_IO );
    printer_IO = -1;
    sprintf( errormessage, "Failed to lock path [%s]", dev.c_str() );
    throw std::runtime_error( errormessage );
  }

  if( tcgetattr( printer_IO, &tty ) < 0 ){
    sprintf( errormessage,
             "Error getting termios settings %s",
             strerror(
               errno ) );
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

  // setup for non-canonical mode
  tty.c_iflag &=
    ~( IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL | IXON );
  tty.c_lflag &= ~( ECHO | ECHONL | ICANON | ISIG | IEXTEN );
  tty.c_oflag &= ~OPOST;

  // fetch bytes as they become available
  tty.c_cc[VMIN]  = 0;
  tty.c_cc[VTIME] = 0;

  if( tcsetattr( printer_IO, TCSANOW, &tty ) != 0 ){
    sprintf( errormessage, "Error setting termios: %s", strerror( errno ) );
    throw std::runtime_error( errormessage );
  }

  printmsg( GREEN( "[PRINTER]" ), "Waking up printer...." );
  std::this_thread::sleep_for( std::chrono::seconds( 5 ) );
  SendHome( true, true, true );
  std::this_thread::sleep_for( std::chrono::milliseconds( 5 ) );

  // Setting speed to be as fast as possible
  SetSpeedLimit( 1000, 1000, 1000 );

  // Setting acceleration to 3x the factory default:
  RunGcode( "M201 X1000 Y1000 Z300\n", 0, 1e5, false );

  return;
}


/**
 * @brief Main function abstraction for sending a gcode command to the session.
 *
 * As a standard in this program, all gcode command string should end in a
 * newline character. This function will parse the gcode string to the printer
 * via the defined interface, and pass the return string of the printer as the
 * return value. Notice that the function will check the return string for the
 * acknowledgement string ("ok" at the start of a line) to know that the
 * command has been executed by the printer. If this acknowledgement string is
 * not received after a wait period, then the command is tried again up to 10
 * times.
 *
 * Notice that exactly when the acknowledgement string is reported will depend
 * on the gcode command in question, and so later functions of abstracting
 * gcode commands should be responsible for choosing an appropriate timeout
 * duration to reduce multiple function calls.
 */
std::string
GCoder::RunGcode( const std::string& gcode,
                  const unsigned     attempt,
                  const unsigned     waitack,
                  const bool         verbose ) const
{
  using namespace std::chrono;

  // static variables
  static const unsigned    maxtry     = 10;
  static const unsigned    buffersize = 65536;
  static const std::string msghead    = GREEN( "[GCODE-SEND]" );

  // Readout data
  char        buffer[buffersize];
  char        msg[1024];
  int         readlen;
  std::string ackstr = "";
  bool        awk    = false;

  // Pretty output
  std::string pstring = gcode;
  pstring[pstring.length()-1] = '\0';// Getting rid of trailing new line

  sprintf( msg,
           "[%s] to USBTERM[%d] (attempt %u)...",
           pstring.c_str(),
           printer_IO,
           attempt );

  if( printer_IO < 0 ){
    throw std::runtime_error( "Printer is not available for commands" );
  }

  if( attempt >= maxtry ){
    sprintf( msg,
             "ACK string for command [%s] was not received after [%d] attempts! The message could be dropped or there is something wrong with the printer!",
             pstring.c_str(),
             maxtry );
    throw std::runtime_error( msg );
  }

  // Sending output
  if( verbose ){ update( msghead, msg ); }
  write( printer_IO, gcode.c_str(), gcode.length() );
  tcdrain( printer_IO );

  high_resolution_clock::time_point t1 = high_resolution_clock::now();
  high_resolution_clock::time_point t2 = high_resolution_clock::now();

  // Checking the output for the acknowledge/completion return
  do {
    readlen = read( printer_IO, buffer, sizeof( buffer )-1 );

    if( readlen > 0 ){
      buffer[readlen] = 1;
      ackstr          = std::string( buffer, buffer+readlen );
      if( check_ack( gcode, ackstr ) ){
        awk = true;
      }
    }
    std::this_thread::sleep_for( std::chrono::milliseconds( 1 ) );
    t2 = high_resolution_clock::now();
  } while( !awk && duration_cast<microseconds>( t2-t1 ).count() < waitack );

  // Checking output
  if( awk ){
    if( verbose ){
      strcat( msg, "... Done!" );
      update( msghead, msg );
    }

    // Flushing the printer buffer after executing the command.
    while( readlen > 0 ){
      readlen = read( printer_IO, buffer, sizeof( buffer )-1 );
      std::this_thread::sleep_for( std::chrono::milliseconds( 5 ) );
    }

    return ackstr;
  } else {
    return RunGcode( gcode, attempt+1, waitack, verbose );
  }
}


/**
 * @brief Private function for checking the acknowledgement string for gcode
 * execution completion.
 *
 * A typically return string after issuing a command will be the:
 * "<return_string>\nok\n", this will be the message that we are looking for.
 * But, the printer will periodically flush the printer settings via the
 * automatic M503 calls that would have the printer accidentally assume the
 * command has been completed when it has not.
 *
 * This function looks at the return message string, and filters on the more
 * obscure commands in our use case, and only returns true if the return message
 * is not a settings report.
 */
static bool
check_ack( const std::string& cmd, const std::string& msg )
{
  auto has_substr = []( const std::string& str, const std::string& sub )->bool {
                      return str.find( sub ) != std::string::npos;
                    };
  if( !has_substr( msg, "ok" ) ){ return false; }
  if( has_substr( msg, "M200" ) ){
    if( !has_substr( cmd, "M503" ) && !has_substr( cmd, "M200" ) ){
      return false;
    }
  }
  return true;
}


/**
 * @brief Sending the gantry to home.
 *
 * The gcode command G28 can have each of the axis sent reset for the axis. This
 * also wipes the current stored axis coordinates to 0
 */
void
GCoder::SendHome( bool x, bool y, bool z )
{
  char cmd[80] = "G28";

  if( !x && !y && !z ){
    return;
  }

  if( x ){
    strcat( cmd, " X" );
    opx = 0;
    cx  = 0;
  }

  if( y ){
    strcat( cmd, " Y" );
    opy = 0;
    cy  = 0;
  }

  if( z ){
    strcat( cmd, " Z" );
    opz = 0;
    cz  = 0;
  }

  // Adding end of line character.
  strcat( cmd, "\n" );

  RunGcode( cmd, 0, 4e9, true );
  clear_update();
}


/**
 * @brief Disabling the stepper motors.
 *
 * The power supply of the gantry is rather noisy, causing issues with the
 * readout system. Disabling the stepper closes the relevant power supplies
 * while the gantry still remembers where it is, at the cost of less stability
 * of the gantry position. Python will be handling for disabling the stepper
 * motors when readout systems are invoked.
 */
void
GCoder::DisableStepper( bool x, bool y, bool z )
{
  if( x ){
    RunGcode( "M18 X E\n", 0, 1e5, false );
  }
  if( y ){
    RunGcode( "M18 Y E\n", 0, 1e5, false );
  }
  if( z ){
    RunGcode( "M18 Z E\n", 0, 1e5, false );
  }
}


/**
 * @brief Enabling the stepper motors.
 *
 * This should be used after the readout has been completed to ereduce the
 * changes of gantry position drifting.
 */
void
GCoder::EnableStepper( bool x, bool y, bool z )
{
  if( x ){
    RunGcode( "M17 X\n", 0, 1e5, false );
  }
  if( y ){
    RunGcode( "M17 Y\n", 0, 1e5, false );
  }
  if( z ){
    RunGcode( "M17 Z\n", 0, 1e5, false );
  }
}


/**
 * @brief Getting a list of settings a the string reported by the gantry.
 */
std::string
GCoder::GetSettings() const
{
  return RunGcode( "M503\n" );
}


/**
 * @brief Setting the motion speed limit (in units of mm/s)
 *
 * There are two steps to setting the motion speeds:
 * 1. Setting the maximum feedrate (M203)
 * 2. Set the feed rate of all future G0 commands (G0 F), this is units of
 *    mm/minutes!
 *
 * In addition we will be setting some hard maximum limits on the motion speed
 * rate:
 * - For x/y: 200mm/s
 * - For z: 30mm/s
 *
 * While setting values to higher is programmatically possible, empirically this
 * is found to make the motion unstable.
 */
void
GCoder::SetSpeedLimit( float x, float y, float z )
{
  static const char  gcode1_fmt[] = "M203 X%.2f Y%.2f Z%.2f\n";
  static const char  gcode2_fmt[] = "G0 F%.2f\n";
  static const float maxv         = 200.0;// Setting the maximum speed
  static const float maxz         = 30.0;// Maximum speed for z axis
  char               gcode[1024];

  // NAN detection.
  if( x != x ){ x = vx; }
  if( y != y ){ y = vy; }
  if( z != z ){ z = vz; }

  if( x > maxv ){ x = maxv; }
  if( y > maxv ){ y = maxv; }
  if( z > maxv ){ z = maxz; }

  sprintf( gcode, gcode1_fmt, x, y, z );
  RunGcode( gcode, 0, 1e5, false );

  const float vmax = std::max( std::max( x, y ), z );
  sprintf( gcode, gcode2_fmt, vmax * 60  );
  RunGcode( gcode, 0, 1e5, false );

  vx = x;
  vy = y;
  vz = z;
}


/**
 * @brief Sending the command for linear motion.
 *
 * This is a very simple interface for the linear motion G0 command, here we
 * will do very minimal parsing on the coordinates:
 *
 * - Make sure that the (x,y,z) coordinates are within physical limitations.
 * - Round the coordinates to the closest 0.1 mm value.
 *
 * Notice that the G0 command will return the ACK string immediate after
 * receiving the command, not after the motion is completed for this reason,
 * additional parsing is required for make sure the motion has completed.
 */
void
GCoder::MoveToRaw( float x, float y, float z, bool verbose )
{
  static const std::string msghead    = GREEN( "[GANTRYPOS]" );
  static const char        move_fmt[] = "G0 X%.1f Y%.1f Z%.1f\n";

  char gcode[128];

  // Setting up target position
  opx = ( x == x ) ?
        x :
        opx;
  opy = ( y == y ) ?
        y :
        opy;
  opz = ( z == z ) ?
        z :
        opz;

  // Rounding to closest 0.1 (precision of gantry system)
  opx = ModifyTargetCoordinate( opx, max_x(), true );
  opy = ModifyTargetCoordinate( opy, max_y(), true );
  opz = ModifyTargetCoordinate( opz, max_z(), true );

  // Running the code
  sprintf( gcode, move_fmt, opx, opy, opz );
  RunGcode( gcode, 0, 1000, verbose );
  if( verbose ){ clear_update(); }

  return;
}


/**
 * @brief Checking whether the gantry has completed the motion to a set of
 * coordinates.
 *
 * The file description interface used for communicating with the gantry does
 * not play well with other interfaces when used as a continuous stream. So
 * rather than having the file interface suspend the thread while the gantry is
 * in motion, we opt to have the gantry perfrom simple one-off checks, and have
 * thread suspension be handled by the higher interfaces.
 *
 * The function will only return false (gantry has completed motion) if the
 * following condition is fulfilled:
 * - The coordinate checking code "M114" is correctly accepted and returned
 * - The return string of the "M114" is in the expected format.
 * - The target coordinates and the current coordinates match to within 0.1(mm)
 *
 * Anything else and the function will return True. Regardless of whether the
 * function returns true or false, the results of the M114 command will be used
 * to update the current gantry coordinates.
 */
bool
GCoder::InMotion( float x, float y, float z )
{
  std::string checkmsg;
  float       a, b, c, temp;// feed position of extruder.
  int         check;
  try {
    checkmsg = RunGcode( "M114\n" );
    check    = sscanf(
      checkmsg.c_str(),
      "X:%f Y:%f Z:%f E:%f Count X:%f Y:%f Z:%f",
      &a,
      &b,
      &c,
      &temp,
      &cx,
      &cy,
      &cz );
  } catch( std::exception& e ){
    return true;
  }

  if( check != 7 ){
    return true;
  }

  // Supposedly the check matching cooridnate
  const double tx = ModifyTargetCoordinate( x, max_x() );
  const double ty = ModifyTargetCoordinate( y, max_y() );
  const double tz = ModifyTargetCoordinate( z, max_z() );

  if( MatchCoord( tx, cx ) && MatchCoord( ty, cy ) && MatchCoord( tz, cz ) ){
    return false;
  } else {
    return true;
  }
}


/**
 * @brief Simple abstraction of the motion command to ensure motion safety.
 *
 * This motion command keeps the z coordinates above 3mm for as much as the
 * motion duration as possible. This help ensures that elements in the gantry
 * head does not impact the platten or the circuit board.
 */
void
GCoder::MoveTo( float x, float y, float z, bool verbose )
{
  static constexpr float min_z_safety = 3;

  if( z < min_z_safety && opz < min_z_safety ){
    MoveToRaw( opx, opy, min_z_safety, verbose );
    std::this_thread::sleep_for( std::chrono::milliseconds( 10 ) );
    MoveToRaw( x,   y,   min_z_safety, verbose  );
    std::this_thread::sleep_for( std::chrono::milliseconds( 10 ) );
    MoveToRaw( x,   y,   z,            verbose );
    std::this_thread::sleep_for( std::chrono::milliseconds( 10 ) );
  } else if( opz < min_z_safety ){
    MoveToRaw( opx, opy, min_z_safety, verbose );
    std::this_thread::sleep_for( std::chrono::milliseconds( 10 ) );
    MoveToRaw( x,   y,   z,            verbose  );
    std::this_thread::sleep_for( std::chrono::milliseconds( 10 ) );
  } else if( z < min_z_safety ){
    MoveToRaw( x, y, min_z_safety, verbose );
    std::this_thread::sleep_for( std::chrono::milliseconds( 10 ) );
    MoveToRaw( x, y, z,            verbose );
    std::this_thread::sleep_for( std::chrono::milliseconds( 10 ) );
  } else {
    MoveToRaw( x, y, z, verbose );
    std::this_thread::sleep_for( std::chrono::milliseconds( 10 ) );
  }
}


/**
 * @brief Simple function to check if two coordinate values are identical, with
 * the gantry resolution of 0.1 mm
 */
bool
GCoder::MatchCoord( double x, double y )
{
  // Rounding to closes 0.1
  x = std::round( x * 10 ) / 10;
  y = std::round( y * 10 ) / 10;
  return x == y;
}


/**
 * @brief Modifying the orignal target cooridnate to somewhere that can be
 * accessed by the gantry
 *
 * Original given some original coodinate value, we return a modified target
 * cooridnate such that:
 * - the return value is always larger than the minimum value 0.1
 * - The return value is always smaller than the given maximum value.
 * - The return value is rounded to the closest 0.1 decimal place.
 *
 * This ensure that given any input coordinate. the target coordinate will
 * always be some value that the physically safe target for the gantry. If the
 * target value is modified in any way other than simple rounding, then an
 * error message will be displayed to ensure notify the user of these
 * modifications.
 */
double
GCoder::ModifyTargetCoordinate( const double original,
                                const double max_value,
                                const bool   verbose )
{
  char message[1024];
  auto rnd = []( double x ){ return std::round( x * 10 ) / 10;};

  double ans = rnd( original ); // rounding to closest
  if( ans < 0.1 ){
    if( verbose ){
      sprintf( message,
               "Target cooridnate values [%.1lf] is below the lower limit 0.1. " "Modifying the target motion cooridnate to 0.1 to avoid damage to the system",
               ans );
      printwarn( message );
    }
    return 0.1;
  } else if( ans > max_value ){
    if( verbose ){
      sprintf( message,
               "Target cooridnate values [%.1lf] is above upper limit [%.1lf]. " "Modifying the target motion cooridnate to [%.1lf] to avoid damage to the system",
               ans,
               max_value,
               max_value );
      printwarn( message );
    }
    return rnd( max_value );
  } else {
    return ans;
  }
}


GCoder::GCoder() :
  printer_IO( -1 ),
  opx       ( -1 ),
  opy       ( -1 ),
  opz       ( -1 )
{}

/**
 * @brief Destructing the GCoder::GCoder object
 *
 * Intensionally adding a verbose system such that the user can debug issue
 * during shutdown.
 */
GCoder::~GCoder()
{
  printf( "Deallocating the gantry controls\n" );
  if( printer_IO > 0 ){
    close( printer_IO );
  }
  printf( "Gantry system closed\n" );
}


IMPLEMENT_SINGLETON( GCoder );
