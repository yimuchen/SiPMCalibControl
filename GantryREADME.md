# Gantry control system instructions

- Last updated: 2021/09/24, Yi-Mu Chen

This machine that you are logged into is the machine used to connection the
gantry control system (running on the Raspberry Pi) in the dark room to the user
and wider internet. Instructions for **operation** should be kept on this machine
here as README files on the control system is reserved for code documentation.
This README servers as the instructions for the main control gateway computer in
the deployed at UMD, and is only added to the GitHub pages here as a means of
persistent backup. The instructions here assumes that the user has basic
knowledge of navigating UNIX file systems over `ssh` and other commands.

## Connecting to and starting the control system

The standard method of connecting to the control system is via ssh. Open a
terminal and login to the control system via the command:

```bash
ssh umdcms@10.42.0.137
```

If successful the prompt should change from a pipeline terminal to a more
traditional bash-style prompt:

```bash
[umdcms@umdpi ~]$
```

Remember that you can always check which machine you are currently operation on
using the `hostname` command.  Before starting up the system, it is good practice
to make sure that high-voltage systems are turned off, or the lights in the dark
room is turned off and the door is properly closed, and the gantry platter is
cleared of clutter before proceeding.

Once in the control system, navigate to the control directory, and start the
control system:

```bash
cd ~/SiPMCalibControl
python3 control.py
```

After some diagnostic information, you should be greeted with the control prompt:

```bash
SiPMCalib>
```

The list of available commands is accessible with the `help` commands, detailed
documentations of a single command can be viewed via the command `help <cmd>`. A
more detailed instruction on how when to use these commands (what sort of data
collection is performed) is will be hosted on the [GitHub
pages](https://yimuchen.github.io/SiPMCalibControl/) of the control software
(full URL: https://yimuchen.github.io/SiPMCalibControl/).

## Analysis of data

Right now (2021.09.24) this connection computer does not have direct access to
the internet. For data analysis you will need to copy the data from the control
system to this connection computer, then copy the data to a USB drive to get the
data onto the cluster for analysis. For more detailed instructions on how to
perform analysis. Refer to the SiPM Calibration analysis software instruction.

## Common settings used for the gantry system

Updated 2021-09-24: Yi-Mu Chen

- Gantry position for rough alignment with SiPM: (x=65, y=115, z=arbitrary)
- Before using the DRS4 readout system (mode=3), set the trigger
  delay to 550 ns:
  ```bash
  drsset --triggerdelay 550
  ```

- PWM settings for a moderate light output at z~10-20, without entering
  constant light output mode:
  ```bash
  pwm -c 0 -d 0.85
  ```

- A nice set of pedestal subtraction range should it be needed:
  ```bash
  --intstart 32 --intstop 102 --pedstart 2 --pedstop 32
  ```

## Generating debugging plots for quick data quality assessment

On the gateway control machine, open a browser and enter into the URL:

http://localhost:9100/debug

You will then be greeted with a dummy GUI session, where all inputs and controls
will not function as no systems used is actually connected to the gateway
machine. (The terminal that you can see is **NOT** an actual terminal that you
can use to control the system inside the dark room.) However, here you can use
the debugging tools to generate some basic quality plots to check for command
setting errors.

First, you will need to get the correct data file to the gateway machine. Then on
the webpage, go to the "Debug plotting" section, put in the full path to the data
file of interest, selection the type of plot that you wish to be displayed and
hit the "request plot" button. The right-hand side should then display a simple
plot representing the data stored in the specified file.

## Notes on editing the code for the control system

Notice that the control code in the `~/SiPMCalibControl` directory will be
periodically wiped to the master [code
branch](https://github.com/yimuchen/SiPMCalibControl). For testing out custom
commands, create a separate `SiPMCalibControl` directory. To commit changes to
the custom commands, file a pull request on GitHub can contact Yi-Mu Chen to
review the pull request. Data files are also not supposed to be stored on the
gantry control Raspberry Pi, please copy data files to `~/Data` on this gantry
control machine.


