#ifndef LOGGER_HPP
#define LOGGER_HPP

#include <stdexcept>
#include <string>

// Main documentation kept in cmod/fmt.py file
/**
 * @defgroup Logging Logging
 * @ingroup hardware
 * @brief Exposing python logging facilities to low level C++ modules
 *
 * @{
 */
extern void printdebug( const std::string& device,
                        const std::string& x );
extern void printinfo( const std::string& device,
                       const std::string& x );
extern void printmsg( const std::string& device,
                      const std::string& x );
extern void printwarn( const std::string& device,
                       const std::string& x );
extern std::runtime_error device_exception( const std::string& device,
                                            const std::string& x  );

extern std::string format_str( const char* exp, ... );
/** @} */
#endif
