/**
 * @brief Functions for streaming G-CODE via USB using termios
 *
 * @file gcode_stream.hpp
 * @date 2018-09-18
 */
#ifndef GCODER_HPP
#define GCODER_HPP

#include <cmath>
#include <string>

struct GCoder
{
  GCoder();
  // GCoder( const std::wstring& dev );
  ~GCoder();

  void init_printer( const std::wstring& dev );

  // Motion functions
  std::string pass_gcode(
    const std::string& gcode,
    const unsigned     attempt = 0,
    const unsigned     waitack = 1e4
    ) const;

  void send_home();

  std::wstring get_settings() const;

  void set_speed_limit(
    float x = std::nanf(""),
    float y = std::nanf(""),
    float z = std::nanf("")
    );

  void move_to_position(
    float x = std::nanf(""),
    float y = std::nanf(""),
    float z = std::nanf("")
    );

public:
  int          printer_IO;
  float        opx, opy, opz;// current position of the printer
  float        vx, vy, vz;// Speed of the gantry head.
  std::wstring dev_path;
};

#endif
