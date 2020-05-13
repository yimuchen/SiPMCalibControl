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
independent design philosophies used for the various interfaces.

### Logger

The logger is a string parsing function.

### G-Code interface for gantry control

Controls of the gantry system involves streaming marlin flavored [g-code][gcode]
to the gantry system over a USB interface. Since we are not using fancy printer
control motions for object shape tracing, we use the standard UNIX C interfaces
to write directory to `/dev/ttyUSBX` object. Additional technology includes
parsing of the response `OK` signal of the printer to know when a motion command
has been completed and to monitor the position of the gantry in real time.
Technical details can be found in the [source code](gcoder.cc).

### Picoscope interface for SiPM data collection

### GPIO interface for ADC, PWM and raw trigger control

### Visual interface for visual processing

## Known issues

- [] Some interface still raise exceptions. This behavior should be removed.

[gcode]: https://marlinfw.org/meta/gcode/