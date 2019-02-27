/**
 * @file logger.hpp
 * @date 2018-10-24
 */
#ifndef LOGGER_PRIVATE_HPP
#define LOGGER_PRIVATE_HPP

#include <map>
#include <string>

class Logger
{
public:
  Logger();
  ~Logger();

  void Update( const std::string&, const std::string& );
  void PrintMessage( const std::string&, const std::string& = "" );
  void ClearUpdate();
  void FlushUpdate();

private:
  std::map<std::string, std::string> _update;
  void screenclear_update();
  void screenflush_update();
  void screenprint_update();
};

#endif
