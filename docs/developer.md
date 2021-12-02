@page developer Developers notes

# Installing the system

Installation should be done on the machine that is capable of interfacing with
both the readout system and the trigger system. Current installation requirements
include:

- Software libraries
  - C++ compiler compatible with C++14 standard
  - [OpenCV 4][opencv]
  - [CMake 3][cmake]
  - [pybind11][pybind11]
  - python 3
    - [numpy][numpy] and [scipy][scipy]: For in-time data processing
    - [flask socketio][flasksocket]: For server hosting
    - [paramiko][paramiko]: For passing output to remote server
- Hardware specific tools
  - [libps5000][picoscope]: For interfacing with the readout oscilloscope
  - [drs][drs]: For interfacing with the readout DRS readout oscilloscope
- For web interface generation
  - [dart-sass][sass] for `css` file generation.
  - [npm][npm] for javascript libraries for the GUI.

The current configuration is designed to work on a [Raspberry Pi 3B+][raspi]
running [Arch Linux ARM7][archarm], and is known to work with a typical Arch
Linux machine for local testing. Equivalent packages for different Linux
distribution should also work, but have not been exhaustively tested. Notice,
that this system is intended to work with some ARM-based headless system. As
network configurations should not be stored online, contact the system
maintainers if you have issues connecting to the system.

## Arch Linux ARM for Deployment

### Dependency installation

Other than the standard developer packages such as a C++ compiler and make, there
are additional packages that need to be installed via pacman.

```
# For ssh tunneling for the CLI interface
pacman -Sy --noconfirm xorg-xauth

# The main C++ libraries and building
pacman -Sy --noconfirm cmake boost opencv pybind11

# For additional package management
pacman -Sy --noconfirm npm git

## The main python packages
pacman -Sy --noconfirm python-scipy python-opencv python-psutil python-paramiko python-flask-socketio

## Additional packages required for opencv, since we are using the high level interface
pacman -Sy --noconfirm qt5-base hdf5-openmpi vtk glew

## For the external javascript libraries
npm install
```

### Optional dependency installation

Not all interfaces are required for the package compile to complete. Which is
useful when testing on personal hardware where one might not want to install the
exotic hardware drivers.


#### Picoscope

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

#### DRS4

The DRS4 is the high resolution readout used for the calibration system
development. This is not going to be added for the final deployment model, but
should still be compilable for testing purposes. You can find the correct version
on the DRS [software page][drs4_download]. THe following are instructions for
adding the DRS 4 package to the external directory:

```bash
cd external
wget https://www.psi.ch/sites/default/files/import/drs/SoftwareDownloadEN/drs-5.0.5.tar.gz

tar zxvf drs-5.0.5.tar.gz
mv drs-5.0.5.tar.gz drs
```

### Interface permission

First ensure that the `i2c` interface and the `pwm` interface has been enabled on
the device. For a Raspberry Pi, add the following lines in to the
`/boot/config.txt` file. Notice if you are using this for local interface
testing, **be careful** with the permission! The `i2c` and `pwm` may be used
other systems in the machine (ex: For the air flow fans). Do _NOT_ enable these
permissions on your personal machine unless you are sure about what the
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
cp external/rules/drs.rules  /etc/udev/rules/
cp external/rules/digi.rules  /etc/udev/rules/
```

If you are running the control software on your laptop, do **NOT** copy the
`digi.rules` file to you laptop unless you know what you are doing. Adjustments
to the hardware permission on typical machines can result in system instability
and potential hardware damage.

## Compiling the control program

The package makes use of the CMake package to run the installation.

```bash
git clone https://github.com/yimuchen/SiPMCalibControl.git
cd SiPMCalibControl

cmake ./
cmake --build ./

python3 control.py     # For interactive CLI interface
python3 gui_control.py # For starting GUI server
```

## Deployment in non-standard systems for development and debugging

Installation instructions above works for x86 Arch Linux installations, and such
work for all UNIX based systems assuming all the dependencies are satisfied. See
the sections above to see the dependencies.

# Contributing to the code

The main code is hosted at this [GitHub repository][github]. Contact the developers for
the pull request if you have something you want to add into the code base!

## Code organization

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

[github]: https://github.com/yimuchen/SiPMCalibControl
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
