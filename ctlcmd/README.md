# Python command line interface

Is directory contain the core of the command line interface. The `controlterm`
class in the [cmdbase.py](cmdbase.py) file extends the [python `Cmd`][pythoncmd]
class to accept `controlcmd` classes in the constructor to define the command
line functions (for example of construction, see the main
[`control.py`](../control.py) file). The `run_cmd` function behaviour is
augmented to handle exceptions raised by the commands routines, and the
`help_cmd` function automatically gets the doc string and the option-parser help
string to reduce code verbosity. The autocompletion function also handles the
option-parser to get easier completion functionalities. The `controlterm` class
instance also contains the class handles of the various interfaces defined in
[`cmod`](../cmod) and [`src`](../src) directory.

Each `controlcmd` classes instance [`argparse`][argparse] python class for the option
parsing, with some common options and parsing pattern defined for decent class
uses. Each controlcmd class instance also contains a reference to the parent
`controlterm` class so that the commands can use the various interfaces as
needed.

The implementation of the commands that is required to run the calibrations are
defined in the various files:

- [digicmd.py](digicmd.py) contains commands for GPIO interface controls.
- [getset.py](getset.py) contains commands for session variable settings.
- [picocmd.py](picocmd.py) contains commands for setting picoscope configurations.
- [motioncmd.py](motioncmd.py) contains commands for gantry motion and the
  majority of luminosity measurement commands.
- [viscmd.py](viscmd.py) contains commands for all visual measurement related
  commands.

[pythoncmd]: https://docs.python.org/3/library/cmd.html
[argparse]: https://docs.python.org/3/library/argparse.html
