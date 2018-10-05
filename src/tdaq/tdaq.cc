#include "tdaq.hpp"

#include <iostream>

constexpr uint16_t LED_PIN = 1 << 8 ;
constexpr uint16_t TRG_PIN = 1 << 16;

std::string measure_once()
{
  std::cout << "[PIN]" << (LED_PIN | TRG_PIN) << " ON!" << std::endl;
  std::cout << "[PIN]" << (LED_PIN | TRG_PIN) << " OFF!" << std::endl;

  // Digital signal processing

  return "RAWDATA";
}