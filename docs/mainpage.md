This official documentation of the SiPM calibaration control program. This
documentation covers both the user-level manual and the software design aspects.
The official code is hosted on [GitHub][github], the analysis of the data
collected by this package is performed by a separate software package that can be
found [here][analysis].

## General start-up instructions for system users

For security reasons, the details for connecting to the various machines will
not be listed in this manual, and should ask the system administrators if there
are connection issues. There are two UNIX-like machines in the system and the
user is responsible to making sure they are using the correct commands on the
correct machine.

### Power on

Power on all low voltage systems required for gantry calibrations, this includes:

- The control Raspberry Pi.
- The 5V power distribution board.
- The tileboard controller (the tileboard receives power through the tileboard
  controller.)
- The analog pulse generator.
- The Picoscope digital oscilloscope.
- The DRS4 digital oscilloscope.
- Additional monitoring scope outside the main dark room.

At this stage, do *not* turn on the high voltage power supply at this point in
time, as this can potentially damage the SiPMs by exposing them to high
intensity background light.

### Permission checks and service start-up

Log into the control Raspberry Pi (contact administrators for how to do this),
and make sure you are on an account with the permission to the key control
devices.

```bash
[user@rpi]$ groups
drs pico i2c gpio video # Output should contain at least these 5 groups.
```

After this, log into the tileboard controller, and start the relevant services
using the following 2 commands:

```bash
[user@TBController]$ $HOME/scripts/startup.sh
[user@TBController]$ $HOME/scripts/serverup.sh
```

The first script would prompt you for a password, while the second script should
be complete without any outputs. Notice the second script starts the services in
the background and should not be executed a second time. If you are unsure
whether the services are already running, run the following commands:

```bash
[user@TBController]$ ps aux | grep zmq_server | grep -v grep
[user@TBController]$ ps aux | grep zmq-server | grep -v grep
[user@TBController]$ ps aux | grep zmq-client | grep -v grep
```

Each command should have a single line for a nominally running service that
looks something like:

```bash
HGCAL_d+  5023  9.9 22.6 876196 462852 ?       Sl   Nov17 569:46 /opt/hexactrl/ROCv2/bin/zmq-server
```

If you wish to terminate the existing services and restart the services, you can
run the following scripts:

```bash
[user@TBController]$ $HOME/scripts/serverup.sh
[user@TBController]$ $HOME/scripts/serverdown.sh
```

### Starting the calibration control program

After the system power on and making sure all required services have been
properly started. You can start 1 of the 2 control programs:

- The [command line interface](@ref cli). This is mainly for the development of
  calibration sequences, individual subsystem controls schemes as well for
  debugging potential issues (or if you are simply more comfortable with a CLI
  interface). The main manual for using the CLI interface can be found at
  [here](@ref cli). If you are attempting to develop a certain calibration
  sequence, be sure to also console the [CLI design](@ref cli_design) pages for
  more detailed information on how to do so. You can start a CLI control program
  instance using the following commands on the control Raspberry Pi:

```bash
[user@RPi]$ cd $HOME/SiPMCalibControl
[user@RPi]$ python3 control.py
```

- The [graphical user interface](@ref gui)(currently under constructions): This
  interface is mainly for batch processing of SiPM calibration during
  production, with additional niceties such as on-the-fly plotting for
  rudimentary data quality management and other progress visualization tools.
  You can start the GUI control program by running the Raspberry Pi, then use
  your favorite web browser to go to the URL: `<RPi.ip.address>:9100`.

```bash
[user@RPi]$ cd $HOME/SiPMCalibControl
[user@RPi]$ python3 gui_control.py
```

## Development instructions

For developers, these following pages mainly aims to highlight the main design
and development philosophies used for the various systems. Due to how the
Doxygen prefering to generate docs pages of individual objects into a single
page, which may cost you more clicks, developers might want to use these pages
as a starting point, and browse the documentations in the various doc strings
and comments directly.

- CLI interface objects and design main reference can be found on this page
  [here](@ref cli_design).
- GUI interface server/client model as well as additional references can be
  found on this [page](@ref gui_design)
- The implementation of various hardware interfaces can be found on this
  [page](@ref hardware)
- The installation of the main program, as well the installation for the various
  external components can be found [here](@ref install).


[github]: https://github.com/UMDCMS/SiPMCalibControl
[analysis]: https://github.com/UMDCMS/SiPMCalib
