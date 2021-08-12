# Installing Instructions

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
pacman -Sy --noconfirm "xorg-xauth" # For ssh tunneling for the CLI interface
pacman -Sy --noconfirm "npm" "git"
pacman -Sy --noconfirm "python-pip" ## For python packages
## Additional packages required for opencv, since we are using the high level interface
pacman -Sy --noconfirm "qt5-base" "hdf5-openmpi" "vtk" "glew"

pip install -r requirements.txt
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
wget https://labs.picotech.com/debian/pool/main/libp/libps5000/libps5000_<version>.deb
ar x libps5000*.deb

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
other systems in the machine (ex: For the air flow fans). Do *NOT* enable these
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
cp external/rules/*.rules  /etc/udev/rules/
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

Installation instructions above works for x86 Arch Linux installations, and up to
the permission settings is what is used to generate the [Dockerfile](Dockerfile)
for testing the interface on the various machines. An entirely local installation
would work if all the dependencies are satisfied. A non-exhaustive list of
dependencies translations are listed below:

[opencv]: https://opencv.org/releases/
[cmake]: https://cmake.org/download/
[pybind11]: https://pybind11.readthedocs.io/en/stable/
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