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

  void InitPrinter( const std::wstring& dev );

  // Raw motion command setup
  std::string RunGcode(
    const std::string& gcode,
    const unsigned     attempt = 0,
    const unsigned     waitack = 1e4,
    const bool         verbose = false
    ) const;

  // Abstaction of actual GCode commands
  void SendHome();

  std::wstring GetSettings() const;

  void SetSpeedLimit(
    float x = std::nanf(""),
    float y = std::nanf(""),
    float z = std::nanf("")
    );

  void MoveTo(
    float      x       = std::nanf(""),
    float      y       = std::nanf(""),
    float      z       = std::nanf(""),
    const bool verbose = false
    );

  // Floating point comparison.
  static bool MatchCoord( double x, double y );

public:
  int          printer_IO;
  float        opx, opy, opz;// current position of the printer
  float        vx, vy, vz;// Speed of the gantry head.
  std::wstring dev_path;
};

#endif
