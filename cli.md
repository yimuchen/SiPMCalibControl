# The CLI interface

Here we have assumed that you have been given the instructions to access a
control session, (some command like `python control.py`) and after which the
command prompt should be switch over to something like `SiPMCalib>`. The most
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
analysis-level commands listed here will have the common output format of an
ASCII file with a various number of columns. The columns will represent the
following:

- `time`: The time stamp at which the line of data is collection relative to the
  initialization of the command.
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
  which will depend on the specific command used to generate the data file in
  question.

Here is a list of command that uses these analysis level output format:

### `lowlightcollect`

UNDER CONSTRUCTION

### `halign`

UNDER CONSTRUCTION

### `zscan`

UNDER CONSTRUCTION

### `visalign`

UNDER CONSTRUCTION

### `timescan`

UNDER CONSTRUCTION

## Raw waveform commands

In certain cases, you might want to take a look at the raw waveform output of the
various readout systems to make sure that the configuration is optimal for the
data collection routine that you are interested in, or to collect data in a way
that is more flexible for data analysis. In this case the user can request that
the waveform data be collected into a file in the following format:

The first line of the file will contain 3 numbers:

- The timescale of each sample bin (ns)
- The number of bits in for each sample bin
- The ADC conversion value for each bit (mV)

The remaining lines would be hexadecimal string representing single collected
waveforms. There are two commands that can be used for getting waveform-like
readouts:

### `drsrun`

UNDER CONSTRUCTION

### `picorunblock`

UNDER CONSTRUCTION

## Readout settings commands

Here is a detailed instruction of how to adjust the various readout system.

### DRS related settings

UNDER CONSTRUCTION

### Picoscope related settings

UNDER CONSTRUCTION

### Visual system related settings

UNDER CONSTRUCTION

### GPIO interface related settings

UNDER CONSTRUCTION

## Calibration of a "board"

Ultimately, the system is expected to run on the HGCAL tileboards. In the code we
abstract the concept of a "board" to simply be a list of photo-detecting compo
