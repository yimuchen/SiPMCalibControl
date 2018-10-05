/**
 * @brief Functions for streaming G-CODE via USB using termios
 *
 * @file gcode_stream.hpp
 * @date 2018-09-18
 */
#ifndef GCODE_STREAM_HPP
#define GCODE_STREAM_HPP

#include <cmath>
#include <string>


/**
 * @brief printer IO setup functions.
 */
extern void init_printer( const std::string& dev );

/**
 * @brief Getting the printer return string. (std::wstring corresponds to
 * python3's str, while std::string corresponds to byte.)
 */
extern std::wstring get_printer_out();

/**
 * @brief sending raw g-code command to terminal.
 */
extern void pass_gcode( const std::string& gcode );

/**
 * @brief Calling the linear motion command to terminal.
 */
extern void move_to_position(
  float x = std::nanf(""),
  float y = std::nanf(""),
  float z = std::nanf("")
  );

#endif
