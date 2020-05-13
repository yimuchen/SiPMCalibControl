# SiPMCalib control software

Software used for the data collection of the SiPM calibration gantry system
developed by UMD. Official documentation is given [here][SiPMCalibTwiki]

## Requirements

Installation should be done on the machine that is capable of interfacing with
both the readout system and the trigger system. Current installation requirements
include:

- Software libraries
  - C++ compiler compatible with C++14 standard
  - OpenCV 4
  - cmake 3
  - boost - python
  - python 3
    - numpy and scipy - For in-time data processing
    - flask socketio - For server hosting
    - paramiko - For passing output to remote server
- Hardware specific tools
  - [libps5000][Picoscope]: For interfacing with the readout oscilloscope
- For web interface generation
  - Install [`sass`][sass] for css file generation.

The current configuration is designed to work on a [Raspberry Pi 3B+][raspi]
running [ArchLinux Arm7][archarm], and is known to work with a typical ArchLinux
machine for local testing.

## Executing the control program

Initiate the interactive command line program using the command:

```bash
python3 control.py
```

You should be greeted with a new command line prompt. For more instruction to how
to use the program, see the [official documentation][SiPMCalibTwiki]. If you have
problems connecting to the Raspberry Pi, see the [CONNECT.md](CONNECT.md) file.

To test

## Installing Instructions

### ArchLinux ARM for Deployment

First ensure that the i2c interface and the pwm interface has been enabled on the
device. For a Raspberry Pi, add the following lines in to the `/boot/config.txt`
file.

```bash
dtparam=i2c_arm=on
```

Notice that the picoscope driver only supports ARM7 and not ARM8. For installing
the standard packages:

```bash
pacman -S boost python opencv python-scipy python-paramiko python-flask-socketio # Architecture independent
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

Then install the package using the regular command:

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

### Local GUI testing on x86 systems

We can test the GUI as a local docker image.

After starting docker, and downloading this repository. Create the docker image using the command:

```bash
docker build  -t sipmcalib:v1 ./
```

After building the image, start the server using the command:

```bash
docker run -t sipmcalib:v1
```

The server itself should start running in the docker container. You can find the
IP of the container using the following commands:

```bash
docker ps
docker inspect --format '{{ .NetworkSettings.IPAddress }}' <CONTAINERID>
```

You can then interact with the GUI by going to `docker_ip:9100` in a browser.

If you are testing changes to the code, you will need to rerun the build command.
It doesn't rebuild the image from scratch, but it does need to rerun compiling
all code in the repository.

[SiPMCalibTwiki]: https://twiki.cern.ch/twiki/bin/viewauth/CMS/UMDHGCalSiPMCalib
[WiringPi]: http://wiringpi.com/
[Picoscope]: https://www.picotech.com/downloads/linux
[Picoscope_MAC]: https://www.picotech.com/downloads
[sas]: https://sass-lang.com/install
[picoscope_download]: https://labs.picotech.com/debian/pool/main/libp/libps5000/
[ADS1x15]: https://github.com/adafruit/Adafruit_CircuitPython_ADS1x15
[raspi]: https://www.raspberrypi.org/products/raspberry-pi-3-model-b-plus/
[archarm]: https://archlinuxarm.org/about/downloads
[Paramiko]: http://www.paramiko.org/
[AUR]: https://aur.archlinux.org/
[yay]: https://aur.archlinux.org/packages/yay/
