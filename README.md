# SiPM Calibration control software

Software used for the data collection of the SiPM calibration gantry system
developed by UMD. Official documentation for users is given
[here][SiPMCalibTwiki]. The documentation for developments is found in the other
markdown files in this repository.

## Executing the control program

Initiate the interactive command line program in the Raspberry Pi using the
command:

```bash
python3 control.py
```

You should be greeted with a new command line prompt. For more instruction to how
to use the program, see the [official documentation][SiPMCalibTwiki]. If you have
problems connecting to the Raspberry Pi, see the [CONNECT.md](CONNECT.md) file.

You can also initiate the GUI interface using the command

```bash
python3 gui_control.py
```

The GUI itself is a web interface hosted on port 9100. To access it, find the IP
of the device hosting the GUI server session, then open a browser and connect to
`device_ip:9100`. Instructions on how to use the documentation is found in the
official documentation.

## Local GUI testing on x86 systems

We can test the GUI as a local docker image.

After installing and starting docker (instructions for various platforms
[here][docker]) and downloading this repository, create the docker image using
the command:

```bash
docker build  -t sipmcalib:v1 ./
```

The actual tag can be anything you want. After building the image, start the
server using the command:

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
all code in the repository. In case you want a more responsive development cycle,
you can change the `CMD` command in the last line of the `Dockerfile` to start a
command line shell instead and trigger the GUI manually.

## Contributing to the software

Documentations for control software development can be found in their various
directories:

- [INSTALL.md](INSTALL.md) Installing instructions, including a list of dependencies
  and additional permission setups.
- [CONNECT.md](CONNECT.md) Additional instructions for network debugging.
- [src](src) Lowest level hardware interfacing with C++.
- [cmod](cmod) Python help classes for calibration session management.
- [ctlcmd](ctlcmd) Python objects for command line interface.
- [server](server) Code for the command line interface (client side and server
  side)

[SiPMCalibTwiki]: https://twiki.cern.ch/twiki/bin/viewauth/CMS/UMDHGCalSiPMCalib
[docker]: https://docs.docker.com/get-docker/
