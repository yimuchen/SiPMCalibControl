/**
 * @brief Defining functions for triggering and DATA aquisition.
 *
 * @file tdaq.hpp
 * @author your name
 * @date 2018-09-24
 */
#ifndef BOARD_HPP
#define BOARD_HPP

#include <string>
#include <map>

struct Board
{
public:
  Board();

  void set_boardtype( const std::string& );
  bool  has_chip( const unsigned ) const ;
  float get_chip_x( const unsigned ) const ;
  float get_chip_y( const unsigned ) const ;

public:
  std::wstring boardid;
  std::wstring boardtype;
  std::map<unsigned, std::pair<float,float> > chip_pos;
  unsigned  op_chip;
};

#endif