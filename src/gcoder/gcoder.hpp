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
  GCoder( const std::string& dev );
  ~GCoder();

  void         init_printer( const std::string& dev );
  std::wstring get_printer_out();

  // Motion functions
  void pass_gcode(
    const std::string& gcode,
    const unsigned wait   = 1e3,
    const unsigned maxtry = 3
  );

  void send_home();

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
  int         printer_IO;
  float       opx, opy, opz;// current position of the printer
  float       vx,vy,vz; // Speed of the gantry head.
  std::string dev_path;
};

#endif
