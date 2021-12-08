#include "pico.hpp"
#include <pybind11/pybind11.h>

PYBIND11_MODULE( pico, m )
{
  pybind11::class_<PicoUnit>( m, "PicoUnit" )
  .def( "instance",
        &PicoUnit::instance,
        pybind11::return_value_policy::reference )
  .def( "init",             &PicoUnit::Init            )
  .def( "settrigger",       &PicoUnit::SetTrigger      )
  .def( "rangemin",         &PicoUnit::VoltageRangeMin )
  .def( "rangemax",         &PicoUnit::VoltageRangeMax )
  .def( "setrange",         &PicoUnit::SetVoltageRange )
  .def( "setblocknums",     &PicoUnit::SetBlockNums    )
  .def( "startrapidblocks", &PicoUnit::StartRapidBlock )
  .def( "isready",          &PicoUnit::IsReady         )
  .def( "waitready",        &PicoUnit::WaitTillReady   )
  .def( "buffer",           &PicoUnit::GetBuffer       )
  .def( "flushbuffer",      &PicoUnit::FlushToBuffer   )
  .def( "dumpbuffer",       &PicoUnit::DumpBuffer      )
  .def( "printinfo",        &PicoUnit::PrintInfo       )
  .def( "adc2mv",           &PicoUnit::adc2mv          )
  .def( "waveformstr",      &PicoUnit::WaveformString  )
  .def( "waveformsum",      &PicoUnit::WaveformSum     )
  .def( "waveformmax",      &PicoUnit::WaveformAbsMax  )
  .def( "rangeA",           &PicoUnit::rangeA          )
  .def( "rangeB",           &PicoUnit::rangeB          )

  // Defining data members as readonly:
  .def_readonly( "device",           &PicoUnit::device           )
  .def_readonly( "presamples",       &PicoUnit::presamples       )
  .def_readonly( "postsamples",      &PicoUnit::postsamples      )
  .def_readonly( "ncaptures",        &PicoUnit::ncaptures        )
  .def_readonly( "timeinterval",     &PicoUnit::timeinterval     )
  .def_readonly( "triggerchannel",   &PicoUnit::triggerchannel   )
  .def_readonly( "triggerdirection", &PicoUnit::triggerdirection )
  .def_readonly( "triggerlevel",     &PicoUnit::triggerlevel     )
  .def_readonly( "triggerdelay",     &PicoUnit::triggerdelay     )
  .def_readonly( "triggerwait",      &PicoUnit::triggerwait      )
  ;
}
