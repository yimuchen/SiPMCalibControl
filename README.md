# SiPM Calibration control software

Software used for the data collection of the SiPM calibration gantry system
developed by UMD. Documentations found in the git repository files will mainly be
used to describe coding and programming technical details regarding the control
software. See the following links for other documentations related to the SiPM
calibration project:

- Typical user operation documentation: this [twiki page][SiPMCalibTwiki]
- Documented results for running the system: this [detector note][SiPMCalibDN]
- Technical details for the analysis program: [here][SiPMCalibAnalysis]

## Contributing to the software

Documentations for control software development can be found in their various
directories:

- [INSTALL.md](INSTALL.md) Installing instructions, including a list of dependencies
  and additional permission setups.
- [CONNECT.md](CONNECT.md) Additional instructions for network debugging.
- [src](src) Lowest level hardware interfacing with C++.
- [cmod](cmod) Python help classes for calibration session management.
- [ctlcmd](ctlcmd) Python objects for command line interface.
- [server](server) Code for the web interface (client side and server side)

[SiPMCalibTwiki]: https://twiki.cern.ch/twiki/bin/viewauth/CMS/UMDHGCalSiPMCalib
[docker]: https://docs.docker.com/get-docker/
[SiPMCalibAnalysis]: https://github.com/yimuchen/SiPMCalib
[SiPMCalibDN]: https://icms.cern.ch/tools/publications/notes/entries/DN/2019/048