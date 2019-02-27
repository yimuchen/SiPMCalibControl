#include "logger_private.hpp"
#include <iostream>
#include <boost/range/adaptor/reversed.hpp>

/**
 * @brief Constructor
 */
Logger::Logger(){}

/**
 * @brief Destroyer
 */
Logger::~Logger(){}

/**
 * @brief Global logging object
 */
extern Logger GlobalLogger;

void
Logger::Update( const std::string& key, const std::string& msg )
{
  screenclear_update();
  _update[key]=msg;
  screenprint_update();
}

void Logger::PrintMessage( const std::string& msg, const std::string& header )
{
  if( header != "" ){
    std::cout << header << " " << std::flush;
  }
  std::cout << msg << std::endl;
}

void Logger::FlushUpdate()
{
  Logger::screenprint_update();
}


void Logger::ClearUpdate()
{
  screenclear_update();
  _update.clear();
}

void Logger::screenclear_update()
{
  static const std::string prevline = "\033[A" ;
  for( const auto& p : boost::adaptors::reverse( _update ) ){
    std::string clear_line( p.first.length()+ p.second.length() +1 , ' ' );
    std::cout << prevline << '\r' << clear_line << '\r' << std::flush ;
  }
}

void Logger::screenprint_update()
{
  for( const auto& p : _update ){
    std::cout << p.first << " " << p.second << std::endl;
  }
}
