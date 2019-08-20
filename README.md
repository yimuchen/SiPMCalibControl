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

For deployment for local testing on personal machines, WiringPi is not needed,
but will require the user to manually setup a trigger system such that the
oscilloscope will terminal nominally. The current configuration is done on a
[Raspberry pi 3B+][raspi] running [ArchLinux Arm7][archarm].

## Installation and run commands

```bash
git clone https://github.com/yimuchen/SiPMCalibControl.git
cd SiPMCalibControl
cmake ./
cmake --build ./

python3 control.py
```

You should be greeted with a new command line prompt. For more instruction to how
to use the program, se the [official documentation][SiPMCalibTwiki].

[SiPMCalibTwiki]: https://twiki.cern.ch/twiki/bin/viewauth/CMS/UMDHGCalSiPMCalib
[WiringPi]: http://wiringpi.com/
[Picoscope]: https://www.picotech.com/downloads/linux
[ADS1x15]: https://github.com/adafruit/Adafruit_CircuitPython_ADS1x15
[raspi]: https://www.raspberrypi.org/products/raspberry-pi-3-model-b-plus/
[archarm]: https://archlinuxarm.org/about/downloads
[Paramiko]: http://www.paramiko.org/