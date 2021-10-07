#ifndef LOGGER_HPP
#define LOGGER_HPP

#include <string>

extern std::string GREEN( const std::string& );
extern std::string RED( const std::string& );
extern std::string YELLOW( const std::string& );
extern std::string CYAN( const std::string& );

extern void update( const std::string& a, const std::string& b );
extern void clear_update();
extern void flush_update();
extern void printmsg( const std::string& header, const std::string& x );
extern void printmsg( const std::string& x );
extern void printwarn( const std::string& x );
extern void printerr( const std::string& x );
extern void setloggingdescriptor( const int );

#endif
