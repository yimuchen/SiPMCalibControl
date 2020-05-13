# Installing Instructions

Installation should be done on the machine that is capable of interfacing with
both the readout system and the trigger system. Current installation requirements
include:

- Software libraries
  - C++ compiler compatible with C++14 standard
  - [OpenCV 4][opencv]
  - [CMake 3][cmake]
  - [boost::python][boostpython]
  - python 3
    - [numpy][numpy] and [scipy][scipy]: For in-time data processing
    - [flask socketio][flasksocket]: For server hosting
    - [paramiko][paramiko]: For passing output to remote server
- Hardware specific tools
  - [libps5000][Picoscope]: For interfacing with the readout oscilloscope
- For web interface generation
  - [sass][sass] for `css` file generation.

The current configuration is designed to work on a [Raspberry Pi 3B+][raspi]
running [Arch Linux ARM7][archarm], and is known to work with a typical Arch
Linux machine for local testing. Equivalent packages for different Linux
distribution should also work, but have not been exhaustively tested.

## Arch Linux ARM for Deployment

### Dependency installation

Other than the standard developer packages such as a C++ compiler and make, there
are additional packages that need to be installed:

```bash
pacman -Sy --noconfirm "cmake" "boost" "opencv"
pacman -Sy --noconfirm "python-numpy" "python-scipy"
pacman -Sy --noconfirm "python-flask-socketio" "python-paramiko"
pacman -Sy --noconfirm "npm" "git"
## Additional packages required for opencv, since we are using the high level interface
pacman -Sy --noconfirm "qt5-base" "hdf5-openmpi" "vtk" "glew"
```

For installing the picoscope driver, download the PKGBUILD file for the x86
picoscope driver.

```bash
wget https://aur.archlinux.org/cgit/aur.git/snapshot/libps5000.tar.gz
tar zxvf libps5000.tar.gz
cd libps5000
```

Then you would need to edit the `PKGBUILD` file in this directory to get the
`armhf` version of the drivers found [here][picoscope_download]. In this, you
will need to edit the `pkgversion`, `source` and the `md5sums` entries in the
`PKGBUILD` file respectively. Notice that the picoscope driver only supports ARM7
and not ARM8, so make sure you are running this package on a compatible ARM
device. Make and install the package using the regular command:

```bash
makepkg -s
pacman -U *.pkg.tar.xz
```

### Interface permission

First ensure that the `i2c` interface and the `pwm` interface has been enabled on
the device. For a Raspberry Pi, add the following lines in to the
`/boot/config.txt` file. Notice if you are using this for local interface
testing, **be careful** with the permission! The `i2c` and `pwm` may be used
other systems in the machine (ex: For the air flow fans). Do *NOT* enable these
permissions on your personal machine unless you are sure about what the
permissions would affect.

```bash
dtparam=i2c_arm=on
```

Next, change the permission of various devices to avoid running the program as
root. For the GPIO/I2C and picoscope interface, create new groups indicating the
usage and add your user to it:

```bash
groupadd -f -r gpio
usermod -G gpio ${USER}
groupadd -f -r i2c
usermod -G i2c ${USER}
groupadd -f -r pico
usermod -G pico ${USER}
```

Then create a `udev` rule to change the permission of the relevant hardware:

```bash
#In /etc/udev/rules.d/99-sipmcontrol.rules

## For the GPIO
SUBSYSTEM=="bcm2835-gpiomem", GROUP="gpio", MODE="0660"
SUBSYSTEM=="gpio", GROUP="gpio", MODE="0660"
SUBSYSTEM=="gpio*", PROGRAM="/bin/sh -c '\
        chown -R root:gpio /sys/class/gpio           && chmod -R 770 /sys/class/gpio;\
        chown -R root:gpio /sys/devices/virtual/gpio && chmod -R 770 /sys/devices/virtual/gpio;\
        chown -R root:gpio sys/devices/platform/soc/*.gpio/gpiochip0/gpio && chmod -R 770 /sys/devices/platform/soc/*.gpio/gpiochip0/gpio;\
        chown -R root:gpio /sys$devpath && chmod -R 770 /sys$devpath\
'"
## For PWM
SUBSYSTEM=="pwm*", PROGRAM="/bin/sh -c '\
        chown -R root:gpio /sys/class/pwm && chmod -R 770 /sys/class/pwm;\
        chown -R root:gpio /sys/devices/platform/soc/*.pwm/pwm/pwmchip* && chmod -R 770 /sys/devices/platform/soc/*.pwm/pwm/pwmchip*\
'"

## For the I2C interface
KERNEL=="i2c-[0-9]*", GROUP="i2c"

## For the picoscope
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0ce9", MODE="664",GROUP="pico"
```

You would need to reboot for the action to take effect. Now, you can compile and
run the program.

```bash
git clone https://github.com/yimuchen/SiPMCalibControl.git
cd SiPMCalibControl

cmake ./
cmake --build ./

python3 control.py     # For interactive CLI interface
python3 gui_control.py # For starting GUI server
```

## Deployment in non-standard systems for development and debugging

Installation instructions above works for x86 Arch Linux installations, and up to
the permission settings is what is used to generate the [Dockerfile](Dockerfile)
for testing the interface on the various machines. An entirely local installation
would work if all the dependencies are satisfied. A non-exhaustive list of
dependencies translations are listed below:

### For Mac OS

The picoscope dependency can be obtained by installing the entire picoscope
software written for Mac. The package manager [`brew`][brew] and the python
package manager [pip][pip] should then be able to install the various libraries
The `CMakeFile.txt` should be able to detect the position of the library.

Known issues would include:

- **`cmake` cannot use boost** In case you run into issue of `cmake` not being
  able to find boost python, prepare `cmake` using the command following command
  instead of the usual `cmake ./` command:

  ```bash
  cmake -D Boost_NO_BOOST_CMAKE:BOOL=ON ./
  ```

- **Library not found for the picoscope** If you have installed the picoscope
  software and the code compiles nominally, but when starting the session it
  program complain about binary symbols or files not found, modify the library
  path variable:

  ```bash
  export DYLD_FALLBACK_LIBRARY_PATH=${DYLD_FALLBACK_LIBRARY_PATH}:"/Applications/PicoScope 6.app/Contents/Resources/lib"
  ```

[opencv]: https://opencv.org/releases/
[cmake]: https://cmake.org/download/
[boostpython]: https://www.boost.org/users/download/
[numpy]: https://numpy.org/
[flasksocket]:https://flask-socketio.readthedocs.io/en/latest/
[scipy]: https://www.scipy.org/scipylib/index.html
[Picoscope]: https://www.picotech.com/downloads/linux
[Picoscope_MAC]: https://www.picotech.com/downloads
[sass]: https://sass-lang.com/install
[picoscope_download]: https://labs.picotech.com/debian/pool/main/libp/libps5000/
[ADS1x15]: https://github.com/adafruit/Adafruit_CircuitPython_ADS1x15
[raspi]: https://www.raspberrypi.org/products/raspberry-pi-3-model-b-plus/
[archarm]: https://archlinuxarm.org/about/downloads
[paramiko]: http://www.paramiko.org/
[brew]: https://brew.sh/
[pip]: https://pip.pypa.io/en/stable/