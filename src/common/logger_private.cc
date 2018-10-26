#include "logger_private.hpp"
#include <iostream>
#include <boost/range/adaptor/reversed.hpp>

/**
 * @brief Constructor
 */
logger::logger(){}

/**
 * @brief Destroyer
 */
logger::~logger(){}

/**
 * @brief Global logging object
 */
extern logger Logger;

void
logger::update( const std::string& key, const std::string& msg )
{
  screenclear_update();
  _update[key]=msg;
  screenprint_update();
}

void logger::printmsg( const std::string& msg, const std::string& header )
{
  std::cout << header << " " << msg << std::endl;
}


void logger::screenclear_update()
{
  static const std::string prevline = "\033[A" ;
  for( const auto& p : boost::adaptors::reverse( _update ) ){
    std::string clear_line( p.first.length()+ p.second.length() +1 , ' ' );
    std::cout << prevline << '\r' << clear_line << '\r' << std::flush ;
  }
}

void logger::screenprint_update()
{
  for( const auto& p : _update ){
    std::cout << p.first << " " << p.second << std::endl;
  }
}

void logger::clear_update()
{
  _update.clear();
}