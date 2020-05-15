# Low level hardware interfaces with C++ and boost python

The code in this software is designed to expose low level hardware control
interfaces to python with C++. C++ is used to allow for some time critical
processes to run (such as with the fast pulsing required for the data collection
trigger), and keep the library requirements to a minimal.

## General design philosophy

For the various interfaces, we expect that there will be issues with the certain
interface not existing, either because the system is in a non-standard
configuration for testing, for the system in question is some personal machine
used for local testing. In such a case, the program in question should **raise
exceptions** during the *initialization* phase, while should simply **do
nothing** (other than perhaps printing an error message) if the user tries to use
the interface regardless. This allows for the user to test the various
functionalities of the system during interface testing.

## Overview of technology for various interfaces

Here we go over the technology used in the various interface, as well as
independent design philosophies used for the various interfaces. All libraries
are compiled using [boost python][boostpython] for exposure to python interface.

### Logger

Files: [logger.cc](logger.cc), [logger.hpp](logger.hpp)

The logger is a library for unifying the output of C++ libraries, this allows for
the same command that requires more constant monitoring (think monitoring the
current position of the gantry) to be flushed and refreshed onto a single line
instead of swamping the terminal with new lines. The library also defines the
decorator strings for allowing colored text to be printed onto the terminal. All
of these uses raw [UNIX escape characters][escapechar] to reduce dependencies.

### G-Code interface for gantry control

Files: [gcoder.cc](gcoder.cc)

Controls of the gantry system involves streaming marlin flavored [g-code][gcode]
to the gantry system over a USB interface. Since we are not using fancy printer
control motions for object shape tracing, we use the standard UNIX C interfaces
to write directory to `/dev/ttyUSBX` object. Additional technology includes
parsing of the response `OK` signal of the printer to know when a motion command
has been completed and to monitor the position of the gantry in real time.
Technical details can be found in the [source code](gcoder.cc).

### GPIO interface for ADC, PWM and raw trigger control

Files: [gpio.cc](gpio.cc)

Controls to the GPIO interface uses raw `sysfs` interfaces to reduce external
library dependencies, and to allow for fast switching for raw trigger controls
(trigger can fire as fast a new nanosecond).

- For references of raw gpio controls (trigger and switches), see the [linux
  kernel documentation][gpio-elinux].
- For references of PWM related controls, see [here][pwm]
- For references of ADS1115s ADC chip controls via i2c see [here][ads1115]
- For additional PIN reference of the raspberry pi, look at the outputs of the
  [wiring-pi][wiringpi] library.

### Visual interface for visual processing

Files: [visual.cc](visual.cc)

We are using OpenCV to process the inputs of a video stream to find a chip. It
uses a relatively simple contouring algorithm and dark square finding algorithm
define the photo-detector position. Details of the implementation are documented
in the function itself.

### Picoscope interface for SiPM data collection

We are using the C++ interface provided by Pico Technology. Essentially we are
compartment the relevant code in the given reference main function to fit our
needs.

## Known issues

- [ ] Some interface still raise exceptions. This behavior should be removed.
- [ ] Need to allow for visual interface to accept images as input when the camera
  is not available for local testing.

[gcode]: https://marlinfw.org/meta/gcode/
[escapechar]: https://en.wikipedia.org/wiki/ANSI_escape_code
[boostpython]: https://www.boost.org/doc/libs/1_73_0/libs/python/doc/html/index.html
[gpio-elinux]: https://elinux.org/GPIO
[pwm]: https://jumpnowtek.com/rpi/Using-the-Raspberry-Pi-Hardware-PWM-timers.html
[ads1115]: http://www.bristolwatch.com/rpi/ads1115.html
[wiringpi]: http://wiringpi.com/