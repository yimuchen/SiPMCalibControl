/**
 * @file logger.hpp
 * @date 2018-10-24
 */
#ifndef LOGGER_PRIVATE_HPP
#define LOGGER_PRIVATE_HPP

#include <map>
#include <string>

class logger
{
public:
  logger();
  ~logger();

  void update( const std::string&, const std::string& );
  void printmsg( const std::string&, const std::string& = "" );
  void clear_update();

private:
  std::map<std::string, std::string> _update;
  void screenclear_update();
  void screenprint_update();
};

#endif
