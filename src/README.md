@defgroup hardware Hardware Interface

The control and manipulation of hardware interfaces is typically implemented in
C/C++, then exposed to python via `pybind11`. The choice of using C/C++ is to
allow for some time critical processes to run (such as the fast pulse required
for the data collection trigger), while keep the library requirements to a
minimal. The `pybind11` related files used to expose the interfaces to python
will be separated into the `cmod` directory with the other low level python
interfaces.

## General design philosophy

For the various interfaces, we expect that there will be issues with the certain
interface not existing, either because the system is in a non-standard
configuration for testing, or the system in question is some personal machine
used for local testing. In such a case, the program in question should **raise
exceptions** during the _initialization_ phase, and should raise an exception
when if the user tries to use the interface regardless. This allows for the user
to test the various functionalities of the system, even when certain interfaces
are not available or not connected.

As the `pybind11` section of the code is separated out into a separate directory.
All interfaces should have their dedicated header file. The documentation within
the header file should be kept to a minimum, with the detailed explanations
placed next to the various functions. We will intentionally choose a different
format compared with python, with both functions and class names in the
`CamelCase` format.

## Overview of technology for various interfaces

Here we go over the technology used in the various interface, as well as
independent design philosophies used for the various interfaces. All libraries
are compiled using [pybind11][pybind11] for exposure to python interface.

### GPIO interface for ADC, PWM and raw trigger control

- Files: [gpio.cc](gpio.cc), [gpio.hpp](gpio.hpp)
- Main documentation: [GPIO](@ref GPIO)

Controls to the GPIO interface uses raw `sysfs` interfaces to reduce external
library dependencies, and to allow for fast switching for raw trigger controls
(trigger can fire as fast a new nanosecond with a period of 1 microsecond).
External documentations of the various systems used:

- For references of raw gpio controls (trigger and switches), see the [linux
  kernel documentation][gpio-elinux].
- For references of PWM related controls, see [here][pwm]
- For references of ADS1115s ADC det controls via i2c see [here][ads1115]
- For additional PIN reference of the Raspberry Pi, look at the outputs of the
  [wiring-pi][wiringpi] library.

### Visual interface for visual processing

- Files: [visual.cc](visual.cc), [visual.hpp](visual.hpp)
- Main documentation: [Visual](@ref Visual)

We are using OpenCV to process the inputs of a video stream to find a detector
element. It uses a relatively simple contouring algorithm and dark square finding
algorithm define the photodetector position. Details of the implementation are
documented in the function itself.

### Picoscope interface for SiPM data collection

- Files: [pico.cc](pico.cc), [pico.hpp](pico.hpp)
- Main documentation: [PicoUnit](@ref PicoUnit)

We are using the C++ interface provided by Pico Technology. Essentially we are
compartment the relevant code in the given reference main function to fit our
needs. The reference code can be found in the open source part of the part of
the [picoscope reference software][picoscope]. Notice that the picoscope
requires proprietary drivers from PicoTechnology, you can find how to install
it in the [install instructions](@ref install)

### DRS4 interfacoe for high resolution SiPM data collection

- Files: [drs.cc](drs.cc), [drs.hpp](drs.hpp)
- Main documentation: [DRSContainer](@ref DRSContainer)

Similar to the picoscope, we are exposing the C-interface of the DRS4, as well
as abstracting various control flows commonly used by the system into single
high-level functions. The reference for the code can be found in the open
source [reference code][drs4_ref]. The nice thing about the DRS4 from a
software point of view is that it is effectively driverless, using only the USB
drivers already in place in most UNIX systems.

[gcode]: https://marlinfw.org/meta/gcode/
[pybind11]: https://pybind11.readthedocs.io/en/stable/
[gpio-elinux]: https://elinux.org/GPIO
[pwm]: https://jumpnowtek.com/rpi/Using-the-Raspberry-Pi-Hardware-PWM-timers.html
[ads1115]: http://www.bristolwatch.com/rpi/ads1115.html
[wiringpi]: http://wiringpi.com/
[picoscope]: https://github.com/picotech/picosdk-c-examples
[drs4_ref]: https://www.psi.ch/en/drs/software-download
