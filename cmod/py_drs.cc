#include "drs.hpp"
#include <pybind11/pybind11.h>

PYBIND11_MODULE( drs, m )
{
  pybind11::class_<DRSContainer>( m, "DRS" )
  // Special singleton syntax, do *NOT* define the __init__ method
  .def( "instance",          &DRSContainer::instance
      , pybind11::return_value_policy::reference )
  .def( "init",              &DRSContainer::Init )
  .def( "timeslice",         &DRSContainer::TimeSlice )
  .def( "startcollect",      &DRSContainer::StartCollect )
  .def( "forcestop",         &DRSContainer::ForceStop )
  // Trigger related stuff
  .def( "set_trigger",       &DRSContainer::SetTrigger )
  .def( "trigger_channel",   &DRSContainer::TriggerChannel )
  .def( "trigger_direction", &DRSContainer::TriggerDirection )
  .def( "trigger_level",     &DRSContainer::TriggerLevel )
  .def( "trigger_delay",     &DRSContainer::TriggerDelay )

  // Collection related stuff
  .def( "set_samples",       &DRSContainer::SetSamples )
  .def( "samples",           &DRSContainer::GetSamples )
  .def( "set_rate",          &DRSContainer::SetRate )
  .def( "rate",              &DRSContainer::GetRate )

  .def( "is_available",      &DRSContainer::IsAvailable )
  .def( "is_ready",          &DRSContainer::IsReady )
  .def( "waveformstr",       &DRSContainer::WaveformStr )
  .def( "waveformsum",       &DRSContainer::WaveformSum )
  .def( "dumpbuffer",        &DRSContainer::DumpBuffer )
  .def( "run_calibrations",  &DRSContainer::RunCalib   )
  ;
}
