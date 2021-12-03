#ifndef LOGGER_HPP
#define LOGGER_HPP

#include <string>
/**
 * @defgroup Logger Logger
 * @ingroup hardware
 * @brief Simple logging facilities across python and C++ modules
 *
 * @details Logging here means the manipulation display of messages on the
 * terminal, not the persistent logging of the system status. Instead of C++'s
 * `std::cout` method and the python `print` method, all terminal printing in
 * the packages should used the facilities provided here to allow for
 * consistent output and piping of the monitoring stream when specified.
 * Functions are also provided to the decorator strings for colored text to be
 * easily printed onto the terminal. All functions should use raw [UNIX escape
 * characters][escapechar] for fancy string manipulation to reduce dependencies
 * on external libraries.
 *
 * The `update` related methods uses a unique header string as the identifier,
 * each time the `update` method is called, the line with the corresponding
 * header string is updated with the new string. This method is particularly
 * useful for commands that require progress reporting without swamping the
 * screen with output lines.
 *
 * [escapechar]: https://en.wikipedia.org/wiki/ANSI_escape_code
 *
 * @{
 */

extern std::string GREEN( const std::string& );
extern std::string RED( const std::string& );
extern std::string YELLOW( const std::string& );
extern std::string CYAN( const std::string& );

extern void printmsg( const std::string& header, const std::string& x );
extern void printmsg( const std::string& x );
extern void printwarn( const std::string& x );
extern void printerr( const std::string& x );
extern void update( const std::string& a, const std::string& b );
extern void clear_update();
extern void flush_update();
extern void setloggingdescriptor( const int );

/** @} */
#endif
