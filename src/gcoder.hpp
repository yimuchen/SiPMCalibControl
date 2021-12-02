#ifndef GCODER_HPP
#define GCODER_HPP

#include <cmath>
#include <memory>
#include <string>

#include "singleton.hpp"

struct GCoder
{
  static const float _max_x;
  static const float _max_y;
  static const float _max_z;

  static float max_x(){ return _max_x; }
  static float max_y(){ return _max_y; }
  static float max_z(){ return _max_z; }

  void Init( const std::string& dev );

  std::string RunGcode( const std::string& gcode,
                        const unsigned     attempt = 0,
                        const unsigned     waitack = 1e4,
                        const bool         verbose = false ) const;

  // Motion command abstraction
  std::string GetSettings() const;
  void        SendHome( bool x, bool y, bool z );
  void        SetSpeedLimit( float x = std::nanf(""),
                             float y = std::nanf(""),
                             float z = std::nanf("") );
  void MoveTo( float      x          = std::nanf(""),
               float      y          = std::nanf(""),
               float      z          = std::nanf(""),
               const bool verbose    = false );
  void MoveToRaw( float      x       = std::nanf(""),
                  float      y       = std::nanf(""),
                  float      z       = std::nanf(""),
                  const bool verbose = false );
  void EnableStepper( bool x, bool y, bool z );
  void DisableStepper( bool x, bool y, bool z );
  bool InMotion( float x, float y, float z );

  // Floating point comparison.
  static bool MatchCoord( double x, double y );

public:
  int         printer_IO;
  float       opx, opy, opz; /** target position of the printer */
  float       cx, cy, cz; /** current position of the printer */
  float       vx, vy, vz; /** Speed of the gantry head. */
  std::string dev_path;

  DECLARE_SINGLETON( GCoder );
};

#endif
