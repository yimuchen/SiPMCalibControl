@defgroup hardware Hardware Interface

# Low level hardware interfaces with C++

The code in this software is designed to expose-low level hardware control
interfaces to python with C++. C++ is used to allow for some time critical
processes to run (such as the fast pulse required for the data collection
trigger), and keep the library requirements to a minimal. The `pybind11` related
files used to expose the interfaces to python will be separated into the
[`cmod`](../cmod) directory with the other low level python interfaces.

## General design philosophy

For the various interfaces, we expect that there will be issues with the certain
interface not existing, either because the system is in a non-standard
configuration for testing, or the system in question is some personal machine
used for local testing. In such a case, the program in question should **raise
exceptions** during the *initialization* phase, and should simply **do nothing**
(other than perhaps printing an error messages) if the user tries to use the
interface regardless. This allows for the user to test the various
functionalities of the system during interface testing.

To help the user be aware of which interfaces are available, the start up and
shutdown of each interface will be verbose (i.e. many `printf` or `cout`
statements).

As the pybind11 section of the code is separated out into a separate directory.
All interfaces should have their dedicated header file. The documentation within
the header file should be kept to a minimum, with the detailed explanations
placed next to the various functions. We will intentionally choose a different
format compared with python, with both functions and class names in the
`CamelCase` format.

## Overview of technology for various interfaces

Here we go over the technology used in the various interface, as well as
independent design philosophies used for the various interfaces. All libraries
are compiled using [pybind11][pybind11] for exposure to python interface.

### Logger

Files: [logger.cc](logger.cc), [logger.hpp](logger.hpp)

The logger is a library for unifying the output of C++ libraries, this allows for
the same command that requires more constant monitoring (think monitoring the
current position of the gantry) to be flushed and refreshed onto a single line
instead of swamping the terminal with new lines. The library also defines the
decorator strings for allowing colored text to be printed onto the terminal. All
of these uses raw [UNIX escape characters][escapechar] to reduce dependencies.

### G-Code interface for gantry control

Files: [gcoder.cc](gcoder.cc), [gcoder](gcoder.hpp)

Controls of the gantry system involves streaming marlin flavored [g-code][gcode]
to the gantry system over a USB interface. Since we are not using fancy printer
control motions for object shape tracing, we use the standard UNIX C interfaces
to write directory to `/dev/ttyUSBX` object. Additional technology includes
parsing of the response `OK` signal of the printer to know when a motion command
has been completed and to monitor the position of the gantry in real time.
Technical details can be found in the [source code](gcoder.cc).

### GPIO interface for ADC, PWM and raw trigger control

Files: [gpio.cc](gpio.cc), [gpio.hpp](gpio.hpp)

Controls to the GPIO interface uses raw `sysfs` interfaces to reduce external
library dependencies, and to allow for fast switching for raw trigger controls
(trigger can fire as fast a new nanosecond with a period of 1 microsecond).

- For references of raw gpio controls (trigger and switches), see the [linux
  kernel documentation][gpio-elinux].
- For references of PWM related controls, see [here][pwm]
- For references of ADS1115s ADC det controls via i2c see [here][ads1115]
- For additional PIN reference of the Raspberry Pi, look at the outputs of the
  [wiring-pi][wiringpi] library.

### Visual interface for visual processing

Files: [visual.cc](visual.cc), [visual.hpp](visual.hpp)

We are using OpenCV to process the inputs of a video stream to find a detector
element. It uses a relatively simple contouring algorithm and dark square finding
algorithm define the photo-detector position. Details of the implementation are
documented in the function itself.

### Picoscope interface for SiPM data collection

Files: [pico.cc](pico.cc), [pico.hpp](pico.hpp)

We are using the C++ interface provided by Pico Technology. Essentially we are
compartment the relevant code in the given reference main function to fit our
needs. The reference code can be found in the open source part of the part of the
[picoscope reference software][picoscope]. Notice that the picoscope requires
proprietary drivers from PicoTechnology, you can find how to install it in the
[install instructions](@ref developer)

### DRS4 interfacoe for high resolution SiPM data collection

Files: [drs.cc](drs.cc), [drs.hpp](drs.hpp)

Similar to the picoscope, we are exposing the C-interface of the DRS4, as well as
abstracting various control flows commonly used by the system into single
high-level functions. The reference for the code can be found in the open source
[reference code][drs4_ref]. The nice thing about the DRS4 from a software point
of view is that it is effectively driverless, using only the USB drivers already
in place in most UNIX systems.

[gcode]: https://marlinfw.org/meta/gcode/
[escapechar]: https://en.wikipedia.org/wiki/ANSI_escape_code
[pybind11]: https://pybind11.readthedocs.io/en/stable/
[gpio-elinux]: https://elinux.org/GPIO
[pwm]: https://jumpnowtek.com/rpi/Using-the-Raspberry-Pi-Hardware-PWM-timers.html
[ads1115]: http://www.bristolwatch.com/rpi/ads1115.html
[wiringpi]: http://wiringpi.com/
[picoscope]: https://github.com/picotech/picosdk-c-examples
[drs4_ref]: https://www.psi.ch/en/drs/software-download