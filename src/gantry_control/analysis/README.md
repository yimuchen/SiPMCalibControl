# Analysis routines

Each file in this directory should contain a single primary function used to
define a calibration routine. This method can either be called as a function
routine or be run standalone, such that we can use the user shell as the
command-line interface (as this opens up the possibility of simply using the
niceties of bash shell for simple programmatic routine control, like looping
over the defined session).

The data collection instructions defined in this directory include:

- `lumi_hscan.py` Performing a gantry horizontal grid scan to determine detector
  position in gantry space.
