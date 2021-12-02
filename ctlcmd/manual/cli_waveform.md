@defgroup cli1_waveform Waveform Extraction commands

@ingroup cli

@brief Command used for detailed waveform extraction.

@details In certain cases, you might want to take a look at the raw waveform
output of the various readout systems to make sure that the configuration is
optimal for the data collection routine that you are interested in, or to collect
data in a way that is more flexible for data analysis. In this case the user can
request that the waveform data be collected into a file in the following format:

The first line of the file will contain 3 numbers:

- The timescale of each sample bin (ns)
- The number of bits in for each sample bin
- The ADC conversion value for each bit (mV)

The remaining lines would be hexadecimal string representing single collected
waveforms. There are two commands that can be used for getting waveform-like
readouts.



@class ctlcmd.drscmd.drsrun

@ingroup cli1_waveform

@details UNDER CONSTRUCTION



@class ctlcmd.picocmd.picorunblock

@ingroup cli1_waveform

@details UNDER CONSTRUCTION
