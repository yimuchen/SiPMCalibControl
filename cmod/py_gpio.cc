#include "gpio.hpp"
#include <pybind11/pybind11.h>

PYBIND11_MODULE( gpio, m )
{
  pybind11::class_<GPIO>( m, "GPIO"  )
  SINGLETON_PYBIND(GPIO)
  .def( "init",        &GPIO::Init                )
  .def( "pulse",       &GPIO::Pulse               )
  .def( "light_on",    &GPIO::LightsOn            )
  .def( "light_off",   &GPIO::LightsOff           )
  .def( "pwm",         &GPIO::SetPWM              )
  .def( "pwm_duty",    &GPIO::GetPWM              )
  .def( "adc_read",    &GPIO::ReadADC             )
  .def( "adc_range",   &GPIO::SetADCRange         )
  .def( "adc_rate",    &GPIO::SetADCRate          )
  .def( "adc_setref",  &GPIO::SetReferenceVoltage )
  .def( "rtd_read",    &GPIO::ReadRTDTemp         )
  .def( "ntc_read",    &GPIO::ReadNTCTemp         )
  .def( "gpio_status", &GPIO::StatusGPIO          )
  .def( "adc_status",  &GPIO::StatusADC           )
  .def( "pwm_status",  &GPIO::StatusPWM           )

  // Static variables
  .def_readonly_static( "ADS_RANGE_6V",    &GPIO::ADS_RANGE_6V )
  .def_readonly_static( "ADS_RANGE_4V",    &GPIO::ADS_RANGE_4V )
  .def_readonly_static( "ADS_RANGE_2V",    &GPIO::ADS_RANGE_2V )
  .def_readonly_static( "ADS_RANGE_1V",    &GPIO::ADS_RANGE_1V )
  .def_readonly_static( "ADS_RANGE_p5V",   &GPIO::ADS_RANGE_p5V )
  .def_readonly_static( "ADS_RANGE_p25V",  &GPIO::ADS_RANGE_p25V )
  .def_readonly_static( "ADS_RATE_8SPS",   &GPIO::ADS_RATE_8SPS )
  .def_readonly_static( "ADS_RATE_16SPS",  &GPIO::ADS_RATE_16SPS )
  .def_readonly_static( "ADS_RATE_32SPS",  &GPIO::ADS_RATE_32SPS )
  .def_readonly_static( "ADS_RATE_64SPS",  &GPIO::ADS_RATE_64SPS )
  .def_readonly_static( "ADS_RATE_128SPS", &GPIO::ADS_RATE_128SPS )
  .def_readonly_static( "ADS_RATE_250SPS", &GPIO::ADS_RATE_250SPS )
  .def_readonly_static( "ADS_RATE_475SPS", &GPIO::ADS_RATE_475SPS )
  .def_readonly_static( "ADS_RATE_860SPS", &GPIO::ADS_RATE_860SPS )
  ;
}
