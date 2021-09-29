# The CLI interface

Here we have assumed that you have been given the instructions to access a
control session, (some command like `python control.py`) and after which the
command prompt should be switch over to something like `SiPMCalib> `. The most
up-to-date technical instructions on what the various command options do can
always be accessed using command `help <cmd>` from within the control command
prompt. The documentation here is mainly going over a broader aspect of what sort
of data you can expect out of various commands, and for what sort of use case
you might want to perform the specific commands.

## Analysis level commands

Here is a list of commands that will typically be used for the individual SiPM
analysis flow, here we assume that the various setup commands has already been
given to you, either by another maintainer or via the other calibration commands
discussed below. Before going into what individual command, note that all
analysis-level commands listed here will have the common output format of a ASCII
file with a various number of columns. The columns will represent the following:

- `time`: The time stamp at which the line of data is collection relative to the
  initalization of the command.
- `detid`: The detector ID number that the measurement is supposed to be
  performed on.
- `x`,
- `y`,
- `z`: The 3 gantry coordinates the measurement is performed on.
- `biasv`: The bias voltage used for the LED pulser, measured by the ADC system.
- `ledtemp`: The temperature of the LED pulser board, measured using a voltage
  divider circuit.
- `sipmtmp`: The temperature of the SiPM board, measured using a voltage divider
  circuit.
- `data`: The remaining columns are all "data" measurements, the exact meaning of
  which will depend on the

## Raw waveform commands

In certain cases, you might want to take a look at the


## Readout settings commands

## Calibration of a "board"
