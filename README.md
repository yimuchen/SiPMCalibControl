# SiPMCalib control software

Software used for the data collection of the SiPM calibration gantry system
developed by UMD. Official documentation is given [here][SiPMCalibTwiki]

## Requirements

Installation should be done on the machine that is capable of interfacing with
both the readout system and the trigger system. Current installation requirements
include:

- Typical tools
  - C++ compiler compatible with C++14 standard
  - cmake
  - python 3
    - additional requires numpy and scipy
  - boost(for boost python)
- Hardware specific tools
  - [ADS1x15 Driver][ADS1x15]: For interfacing with pico-ammeter readout
  - [libps5000][Picoscope]: For interfacing with the readout oscilloscope
  - [WiringPi][WiringPi]: For trigger control via GPIO
  - [Paramiko][Paramiko]: For data transfer over ssh
- For web interface generation
  - Install `sass` for css file generation.

For deployment for local testing on personal machines, WiringPi and ADS1x15 is
not needed. But local testing will require the user to manually setup a trigger
system such that the oscilloscope will terminal nominally. The current
configuration is done on a [Raspberry pi 3B+][raspi] running [ArchLinux
Arm7][archarm], and is known to work with a typical ArchLinux machine.

## Executing the control program

Initiate the program using the command

```bash
python3 control.py
```

You should be greeted with a new command line prompt. For more instruction to how
to use the program, se the [official documentation][SiPMCalibTwiki]. If you have
problems connecting to the raspberry Pi, see the [CONNECT.md](CONNECT.md) file.

## Installing Instructions

In general, the control software requires python3 and opencv-4.0, and the driver
for the picoscope. The following machine configurations have been tested.

### ArchLinux ARM for Deployment

First ensure that the i2c interface and the pwm interface has been enabled on the
device. For as raspberry pi, add the following lines in to the `/boot/config.txt`
file.

```bash
dtparam=i2c_arm=on


```

Notice that the picoscope driver only supports ARM7 and not ARM8. For installing
the standard packages:


```bash
pacman -S boost python opencv python-scipy python-paramiko # Architecture independent
pacman -S wiringpi #Only on pi
pip3 install adafruit-circuitpython-ads1x15 # Only on Pi
```


For installing the picoscope driver, download the PKGBUILD file for the x86
picoscope driver.

```bash
wget https://aur.archlinux.org/cgit/aur.git/snapshot/libps5000.tar.gz
tar zxvf libps5000.tar.gz
cd libps5000
```

The you would need to edit the `PKGBUILD` file in this directory to get the
`armhf` version of the drivers found [here][picoscope_download]. In this, you
will need to edit the `pkgversion`, `source` and the `md5sums` entries in the
`PKGBUILD` file respectively.

The install the package using the regular command:

```bash
makepkg -si
pacman -U *.pkg.tar.xz
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

python3 control.py
```

### ArchLinux (standard x86) for local testing

For the installing of standard packages:

```bash
pacman -S boost python opencv python-scipy python-paramiko
```

For installing the picoscope driver

```bash
wget https://aur.archlinux.org/cgit/aur.git/snapshot/libps5000.tar.gz
tar zxvf libps5000.tar.gz
cd libps5000
makepkg -si
pacman -U *.pkg.tar.xz
```

Then, compile the control software:

```bash
git clone https://github.com/yimuchen/SiPMCalibControl.git
cd SiPMCalibControl

cmake ./
cmake --build ./
```

Check if it can run using:

```bash
python3 control.py
```

### Mac with Homebrew for local testing

Manually download the picoscope driver from [HERE][Picoscope_MAC]. Then run the
following commands:

```bash
brew install cmake python3 boost boost-python3 opencv
pip3 install paramiko
pip3 install scipy
```

The compile the control software

```bash
git clone https://github.com/yimuchen/SiPMCalibControl.git
cd SiPMCalibControl

cmake -D Boost_NO_BOOST_CMAKE:BOOL=ON ./
cmake --build ./
```

You would need to export the library search variable:

```bash
export DYLD_FALLBACK_LIBRARY_PATH=${DYLD_FALLBACK_LIBRARY_PATH}:"/Applications/PicoScope 6.app/Contents/Resources/lib"
```

Then run:

```bash
python3 control.py
```

[SiPMCalibTwiki]: https://twiki.cern.ch/twiki/bin/viewauth/CMS/UMDHGCalSiPMCalib
[WiringPi]: http://wiringpi.com/
[Picoscope]: https://www.picotech.com/downloads/linux
[Picoscope_MAC]: https://www.picotech.com/downloads
[picoscope_download]: https://labs.picotech.com/debian/pool/main/libp/libps5000/
[ADS1x15]: https://github.com/adafruit/Adafruit_CircuitPython_ADS1x15
[raspi]: https://www.raspberrypi.org/products/raspberry-pi-3-model-b-plus/
[archarm]: https://archlinuxarm.org/about/downloads
[Paramiko]: http://www.paramiko.org/
[AUR]: https://aur.archlinux.org/
[yay]: https://aur.archlinux.org/packages/yay/
