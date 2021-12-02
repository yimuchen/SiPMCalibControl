@defgroup cli0_analysis SiPM Analysis-Level commands

@ingroup  cli

@brief Command typically used for single SiPM analysis level, assume nominal
calibration processes.

Here is a list of commands that will typically be used for the individual SiPM
analysis flow, here we assume that the various setup commands has already been
given to you, either by another maintainer or via the other calibration commands
discussed below. Before going into what individual command, note that all
analysis-level commands listed here will have the common output format of an
ASCII file with a various number of columns. The columns will represent the
following (for more documentation of output formats see the [`savefilecmd`](@ref
 ctlcmd.cmdbase.savefilecmd) class)

- `time`: The time stamp at which the line of data is collection. Time is
  measured relative to the initialization of the command.
- `detid`: The detector ID number that the measurement is supposed to be
  performed on (this many not be used).
- `x`,`y`, `z`: The 3 gantry coordinates the measurement is performed on.
  Measured according to the internal coordinates system of the gantry.
- `biasv`: The bias voltage used for the LED pulser, measured by the ADC system.
- `ledtemp`: The temperature of the LED pulser board, measured using a voltage
  divider circuit and the ADC system.
- `sipmtmp`: The temperature of the SiPM board, measured using a voltage divider
  circuit and the ADC system.
- `data`: The remaining columns are all "data" measurements, the exact meaning of
  which will depend on the specific command used to generate the data file in
  question.

The command will typically share the following same similar command arguments

- Coordinate specification arguments:

  `-x`, `-y`, `-z`: Is typically used to specify the "central" operation
  coordinate value in gantry coordinates with units of millimeters. If either of
  the coordinates is not specified, then the current position is assumed as the
  designed coordinate values. Notice that there will be additional case handling
  if we are using predefined or calibrated coordinates of detector-on-board. See
  the "Calibration of a board" section below for more information. If you are
  calibration for single photodetectors, it is good practice to always specify
  the coordinates.

- Readout settings arguments

  - `--mode [int]`:  Which readout system should be used for data collection.
    Currently, the following subsystems have been implemented. Notice that each
    subsystem has additional settings such as trigger, timing and voltage range
    that is not handled here. These should be properly set before running
    analysis level.
    - `1`: The screen-less Picoscope. For additional settings, see the "Picoscope
      related settings" section below.
    - `2`: Treating the ADC readout value as a photodetector readout. Notice that
      right now, most channels of the ADC chip is used for system status
      monitoring, so be sure that the readout channel is actually reading a real
      photodectector.
    - `3`: The DRS4 screen-less oscilloscope. For additional settings, see the
      "DRS related settings" section below.

  - `--channel [int]`: The channel of the readout system to take for the data.
    Good practice to double-check that the readout system is connected to the
    channel of interest.

  - `--samples [int]`: The number of waveforms to take before for the readout average.



@class ctlcmd.motioncmd.lowlightcollect

@ingroup cli0_analysis

@details This is a test



@class ctlcmd.motioncmd.halign

@ingroup cli0_analysis

@details This is a test




@class ctlcmd.motioncmd.zscan

@ingroup cli0_analysis

@details This is a test



@class ctlcmd.viscmd.visualhscan

@ingroup cli0_analysis

@details This is a test


@class ctlcmd.viscmd.visualcenterdet

@ingroup cli0_analysis

@details This is a test




@class ctlcmd.viscmd.visualmaxsharp

@ingroup cli0_analysis

@details This is a test
