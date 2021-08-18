#include "gcoder.hpp"
#include <pybind11/pybind11.h>

PYBIND11_MODULE( gcoder, m )
{
  pybind11::class_<GCoder>( m, "GCoder" )
  // Explicity hiding the constructor instance, using just the instance method
  // for getting access to the singleton class.
  .def( "instance",        &GCoder::instance
      , pybind11::return_value_policy::reference  )
  .def( "init",            &GCoder::Init          )
  // Hiding functions from python
  .def( "run_gcode",       &GCoder::RunGcode       )
  .def( "getsettings",     &GCoder::GetSettings    )
  .def( "set_speed_limit", &GCoder::SetSpeedLimit  )
  .def( "moveto",          &GCoder::MoveTo         )
  .def( "enablestepper",   &GCoder::EnableStepper  )
  .def( "disablestepper",  &GCoder::DisableStepper )
  .def( "in_motion",       &GCoder::InMotion       )
  .def( "sendhome",        &GCoder::SendHome       )
  .def_readwrite( "dev_path", &GCoder::dev_path )
  .def_readwrite( "opx",      &GCoder::opx )
  .def_readwrite( "opy",      &GCoder::opy )
  .def_readwrite( "opz",      &GCoder::opz )
  .def_readwrite( "cx",      &GCoder::cx )
  .def_readwrite( "cy",      &GCoder::cy )
  .def_readwrite( "cz",      &GCoder::cz )

  // Static methods
  .def_static( "max_x", &GCoder::max_x )
  .def_static( "max_y", &GCoder::max_y )
  .def_static( "max_z", &GCoder::max_z )
  ;
}
