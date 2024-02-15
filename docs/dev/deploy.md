# Deploying the Calibration Control programs

Dependencies required to run the program is handled by [`conda`][conda]. Notice
that hardware interactions is [abstracted away][hardware] for the control
program, and this package is mainly concerned with the data flow handling
processes. Deploying the package should not require package to be explicitly
installed other than `conda`, and the custom code base hosted in GitHub.

```bash
# Getting the custom code base
git clone https://github.com/UMDCMS/SiPMCalibControl
git clone https://github.com/UMDCMS/GantryMQ
git clone https://github.com/UMDCMS/sipmpdf

# Creating and starting the conda virtual envrionment
conda env create --file SiPMCalibControl/environment.yml
conda activate gantry_control

# Installing the C++ requirements of the control program
cd SiPMCalibControl
CXX=$(which g++) LD_LIBRARY_PATH=${CONDA_PREFX}/lib cmake ./ && cmake --build ./
cd ../

# Installing the packages as python packages (do not change the ordering!!)
python -m pip install -e ./GantryMQ
python -m pip install -e ./sipmpdf
python -m pip install -e ./SiPMCalibControl

# Creating the GUI client
cd SiPMCalibControl/src/gui_client/
npm i # Install javacript dependencies
python run_build.py # Building the actu
```

Notice that any modifications to the python modules will be automatically to
the environment (though you will need to restart any running python scripts for
the edits to take effect). For the GUI client, you can run the
`src/gui_client/run_build.py` at any time and refresh the corresponding
web-page.


Here you should be able to run the various programs provided in the repository:
For instructions of what programs are available and what is required to run
these, please refer to the [manual](../manual).

## Contributing to the code

The main code base is hosted at this [GitHub repository][github]. Contact the
developers for the pull request if you have something you want to add into the
code base!

### Code organization

Documentations for control software development can be found in their various
directories:

- Documentation of the hardware interfaces and other minimal dependency helper
  objects/functions are handled by separate libraries:
  - For gantry related projects, consult the [GantryMQ][hardware] repository
  - For the basics of tileboard tester interactions, see [this
    repository][tbt], for our custom implementation, see the
    `src/gantry_control/tbc` directory.
- Documentation of the management of the various control objects can be found
  in the `src/gantry_control/cli` directory. 
- Documentation of analysis routines can be found in the
  `src/gantry_control/analysis` directory. 
- For additional object management required for hosting a GUI session, see the
  `src/gantry_control/gui_server` directory.
- For the client side GUI session, see the `src/gui_client`

[conda]: https://conda.io/projects/conda/en/latest/user-guide/install/index.html
[hardware]: https://github.com/UMDCMS/GantryMQ
[tbt]: https://gitlab.cern.ch/hgcal-daq-sw/hexactrl-script
