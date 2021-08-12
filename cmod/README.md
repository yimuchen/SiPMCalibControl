# Python modules for session management helper

Here are a bunch of python modules to help handle session variables, written in
python since most of these libraries either is for string parsing for
configuration files, or simply uses high level system library such as specialized
IO handling. Most of these are relatively simple single file classes that handle
in single task. Also note that the C++ libraries in the [`src` directory](../src)
will be placed here, to simplify the python call. For the sake of simplifying the
make process, the C++ files for pybind11 are also placed here.

## Overview for libraries

### [board.py](board.py)

Simple container for a board in a calibration session. Basically a list of
photo-detector ids, and a map that records the default and measure coordinates of
the photo-detectors. Can save and read results in json format.

### [readout.py](readout.py)

Python abstraction of the readout. This makes it so that the commands in the can
obtain the readout of a photo-detector in a unified interface, either from the
ADC interface, the picoscope or a mathematical model for testing. This function
also handles the averaging and error estimation for reading out data in multiple
samples.

### [sighandle.py](signal.py)

Simple class for overwriting default signal handling behavior so that actions like
'CTL+C' can be used to exit a calibration process safely.

### [sshfiler.py](sshfiler.py)

Simple class for abstracting opening a file to some server over SSH. Handing for
passing file directory over to Tier 3 for hosting. Also opens an accompanying
file in 'read' mode to progress extraction.

### [actionlist.py](actionlist.py)

Simple class for defining a set of action lists. Basically a parser for a simple
json file corresponding for a user action “tag” and a user action “message” to
pause a session indefinitely until the user confirmation input.
