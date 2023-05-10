@page install Installation instructions

## Installing the Calibration Control programs

This is the program that is maintained by this packages by the developers at the
University of Maryland. Installation should be done on the machine that is
capable of interfacing with both the readout system and the trigger system.
Current installation requirements include:

- Software libraries
  - C++ compiler compatible with C++14 standard (using g++ as default)
  - [OpenCV 4][opencv]: For visual processing routines (webcams that can be used
    in the system generally does not require special driver systems)
  - [CMake 3][cmake]: For handling the build environemtn
  - [pybind11][pybind11]: For generating python binding for code written in C++
  - Python 3: Main language used for high-level interface design.
    - [numpy][numpy] and [scipy][scipy]: For in-time data processing.
    - [flask socketio][flasksocket]: For GUI server hosting.
    - [paramiko][paramiko]: For interaction of machines over network
      connections, required for the tileboard controller system controls, as
      well as sending the calibration outputs to remote servers for detailed
      data processing.
    - [zmq][python-zmq]: For interacting with the tileboard controller server instances.
    - [yaml][python-yaml]: For interacting with the tileboard controller configurations.
    - [uproot][python-uproot]: For processing the data returned by the tileboard controller.
- Hardware specific tools:
  - [libps5000][picoscope]: For interfacing with the Picoscope oscilloscope for data readout.
  - [drs][drs]: For interfacing with the readout DRS oscilloscope for data readout.
- For web interface generation
  - [dart-sass][sass] for `css` file generation.

The current configuration is designed to work on a [Raspberry Pi 3B+][raspi]
running [Arch Linux ARM7][archarm], and is known to work with a typical Arch
Linux machine for local testing. Equivalent packages for different Linux
distribution should also work, but have not been exhaustively tested. Notice,
that this system is intended to work with some ARM-based headless system. As
network configurations should not be stored online, contact the system
maintainers if you have issues connecting to the system.

### Arch Linux ARM for Deployment

#### Dependency installation

First, we can set up to code repository you can clone the main repository by
cloning the git repository:

```bash
git clone https://github.com/UMDCMS/SiPMCalibControl.git
cd SiPMCalibControl
```

But do not attempt to compile or run the program just yet, as additional
dependencies need to be installed. Other than the standard developer packages
such as a C++ compiler and make, there are additional packages that need to be
installed via the `pacman` command for ArchLinux.

```bash
# For ssh tunneling for the CLI interface
pacman -Sy --noconfirm xorg-xauth

# The main C++ libraries and building
pacman -Sy --noconfirm cmake opencv pybind11 fmt

# For additional package management
pacman -Sy --noconfirm git

## The main python packages
pacman -Sy --noconfirm python-scipy          \
                       python-opencv         \
                       python-psutil         \
                       python-paramiko       \
                       python-flask-socketio \
                       python-pyzmq          \
                       python-yaml           \
                       python-tqdm           \
                       python-uproot

## Additional packages required for opencv, since we are using the high level interface
pacman -Sy --noconfirm qt5-base hdf5-openmpi vtk glew
```

Let the package developers know if you run into any issues with any of the
install commands.

#### Hardware specific dependency installation

Not all interfaces are required for the package compile to complete. Which is
useful when testing on personal hardware where one might not want to install the
exotic hardware drivers. External package will be pulled to the `/external`
directory of the directory.

##### Picoscope

The picoscope is a testing readout solution used during the calibration system
development. This is not going to be added to the final deployment model, but
should still be used for testing purposes. You can find the correct version
[here][picoscope_download]. The following are instruction for added the required
instruction for adding the picoscope to the external directory to be installed.

```bash
cd external
wget https://labs.picotech.com/debian/pool/main/libp/libps5000/libps5000_version.deb
ar x libps5000_version.deb

tar xvf data.tar.xz
mv opt/picoscope ./

## Clean up stray files
rm control.tar.gz
rm debian-binary
rm usr/ -rf
rm opt/ -rf
```

##### DRS4

The DRS4 is the high resolution readout used for the calibration system
development. This is not going to be added for the final deployment model, but
should still be compilable for testing purposes. You can find the correct version
on the DRS [software page][drs4_download]. The following are instructions for
adding the DRS 4 package to the external directory:

```bash
cd external
wget https://www.psi.ch/sites/default/files/import/drs/SoftwareDownloadEN/drs-5.0.5.tar.gz

tar zxvf drs-5.0.5.tar.gz
mv drs-5.0.5 drs
```

#### Interface permission

First ensure that the `i2c` interface and the `pwm` interface has been enabled
on the device. For a Raspberry Pi, add the following lines in to the
`/boot/config.txt` file. Notice if you are using this for local interface
testing, **be very careful** with the permissions as the `i2c` and `pwm` may be
used other systems in the machine (ex: For the air flow fans). Do _NOT_ enable
these permissions on your personal machine unless you are sure about what the
permissions would affect. Note that the `dtparam` line must added after the
kernel loading line.

```bash
dtoverlay=pwm-2chan
dtparam=i2c_arm=on
```

Next, change the permission of various devices to avoid running the program as
root. For the GPIO/I2C and picoscope interface, create new groups indicating the
usage and add your user to it:

```bash
groupadd -f -r gpio
usermod -a -G gpio ${USER}
groupadd -f -r i2c
usermod -a -G i2c ${USER}
groupadd -f -r pico
usermod -a -G pico ${USER}
groupadd -f -r drs
usermod -a -G drs ${USER}
```

Then create a `udev` rule to change the permission of the relevant hardware. Copy
the provided rules file to the `/etc/udev/rules.d` directory. A reboot is
required for the results to take effect.

```bash
cp external/rules/pico.rules  /etc/udev/rules/
cp external/rules/drs.rules   /etc/udev/rules/
cp external/rules/digi.rules  /etc/udev/rules/
```

If you are running the control software on your laptop, do **NOT** copy the
`digi.rules` file to you laptop unless you know what you are doing. Adjustments
to the hardware permission on typical machines can result in system instability
and potential hardware damage.

### Compiling the control program

The package makes use of the CMake package to run the installation.

```bash
git clone https://github.com/yimuchen/SiPMCalibControl.git
cd SiPMCalibControl

cmake ./
cmake --build ./

python3 control.py     # For interactive CLI interface
python3 gui_control.py # For starting GUI server
```

### Deployment in non-standard systems for development and debugging

Installation instructions above works for x86 Arch Linux installations, and such
work for all UNIX based systems assuming all the dependencies are satisfied. See
the sections above to see the dependencies. In addition, we provide a docker
image for people looking to develop locally in a non-standard environment.

#### Docker instructions

This is mainly used for testing interface development. While the docker script
will copy the hardware interface packages for compilation, the interactive
interface is set up such that it will still operate if the various control
components are not available.

To build a docker image and start the docker image.

```bash
docker build --tag sipmcalib_control --rm ./
docker run -it -p 9100:9100 sipmcalib_control:latest
```

This should start an interactive bash session, where once can then start the
CLI/GUI interfaces with the python commands

```bash
python control.py
python gui_control.py
```

Notice that the files in the docker session are a copy and not a mount, meaning
that if you should edit the file outside the docker session and rebuild the
docker session to allow for data to be passed to docker session. If you did not
modify the C++ files, you should not need to recompile.

## Installing software and firmware for the tileboard controller

The second-largest components of the calibration system is the interface with
the tileboard controller, used to communicate with the HGCAL systems. The
requirements here are maintained by the broader HGCAL community, mainly by the
University of Minnesota. With most of the instructions found for their
[read-the-docs page][hgcal-quickstart].

To avoid out-of-date information, we will not be including software installation
instructions here, but rather the administrators will be responsible for
ensuring the software and firmware on the tileboard controller is up-to-date.
The 3 key pieces of software that is required for the main calibration control
sequence to work would include:

- The fast controls interaction server (usually named `zmq-server`)
- The fast data pulling "client" (usually named the `zmq-client`)
- The slow controls and readout server (usually named the `zmq_server`, notice
  the difference in hyphenation).

Turn-key solutions for starting/stopping the tileboard control software programs
are kept in the `scripts/tbcontroller` directory.

## Contributing to the code

The main code base is hosted at this [GitHub repository][github]. Contact the
developers for the pull request if you have something you want to add into the
code base!

### Code organization

Documentations for control software development can be found in their various
directories:

- Documentation of the Hardware interfaces and other minimal dependency helper
  objects/functions can be found [here](@ref hardware). The `src` directory
  contains the C++ implemented classes, and the `cmod` directory contains the
  python objects along with the python bindings for the C++ classes.
- Documentation of the CLI interface can be found [here](@ref cli_design). Files for
  this is typically found in the `ctlcmd` directory.
- Documentation of the GUI interface can be found [here](@ref gui_design). Files for
  this is typically found in the `server` directory:
  - The server side code is found in the `server/sockets` directory.
  - The client side code is found in the `server/static/js` directory.
  - Styling file will likely not get their own documentation.

[github]: https://github.com/UMDCMS/SiPMCalibControl
[opencv]: https://opencv.org/releases/
[cmake]: https://cmake.org/download/
[pybind11]: https://pybind11.readthedocs.io/en/stable/
[numpy]: https://numpy.org/
[flasksocket]: https://flask-socketio.readthedocs.io/en/latest/
[scipy]: https://www.scipy.org/scipylib/index.html
[picoscope]: https://www.picotech.com/downloads/linux
[picoscope_mac]: https://www.picotech.com/downloads
[sass]: https://sass-lang.com/install
[picoscope_download]: https://labs.picotech.com/debian/pool/main/libp/libps5000/
[ads1x15]: https://github.com/adafruit/Adafruit_CircuitPython_ADS1x15
[raspi]: https://www.raspberrypi.org/products/raspberry-pi-3-model-b-plus/
[archarm]: https://archlinuxarm.org/about/downloads
[paramiko]: http://www.paramiko.org/
[brew]: https://brew.sh/
[pip]: https://pip.pypa.io/en/stable/
[drs]: https://www.psi.ch/en/drs/software-download
[drs4_download]: https://www.psi.ch/en/drs/software-download
[npm]: https://www.npmjs.com/
[python-zmq]: https://pyzmq.readthedocs.io/en/latest/
[python-uproot]: https://uproot.readthedocs.io/en/latest/
[python-yaml]: https://pyyaml.org/wiki/PyYAMLDocumentation
[hgcal-quickstart]: https://readthedocs.web.cern.ch/display/HGCELE/Tileboard+Tester+V2+Quick+Start+Guide
