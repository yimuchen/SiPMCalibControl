#include "board.hpp"
#include <iostream>
#include <vector>

#include <boost/format.hpp>
#include <boost/property_tree/json_parser.hpp>

Board::Board()
{}

void
Board::set_boardtype( const std::string& jsonfile )
{
  // Cleaning existing settings
  boardtype = std::wstring(jsonfile.begin(),jsonfile.end());
  chip_pos.clear();

  boost::property_tree::ptree tree;
  boost::property_tree::read_json( jsonfile, tree );

  for( const auto& it : tree ){
    const unsigned chipid = std::stoi( it.first );
    std::vector<float> pos;

    for( const auto& posit : it.second ){
      pos.push_back( posit.second.get_value<float>() );
    }

    // Adding error for values other than x-y pairs
    if( pos.size() < 2 ){
      std::cout << boost::format(
        "Warning! Position for chip-id %d is missing coordinates! Skipping..."
          ) % chipid << std::endl;
      return;
    } else if( pos.size() > 2 ){
      std::cout << boost::format(
        "Warning! Position of chip-id %d has extra coordinates! Truncating..."
          ) % chipid << std::endl;
    }

    std::pair<float, float> pc( pos.at( 0 ), pos.at( 1 ) );

    // Adding warning for redefined position
    if( chip_pos.count( chipid ) ){
      std::cout << boost::format(
        "Warning! Position for chip-id %d redefined! Using the latter position"
          ) % chipid << std::endl;
    }

    chip_pos[chipid] = pc;
  }

  return;
}

bool
Board::has_chip( const unsigned id ) const
{
  return chip_pos.count( id );
}


float
Board::get_chip_x( const unsigned id ) const
{
  return chip_pos.at( id ).first;
}

float
Board::get_chip_y( const unsigned id ) const
{
  return chip_pos.at( id ).second;
}
