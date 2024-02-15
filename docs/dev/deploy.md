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
CXX=$(which g++) cmake ./ && cmake --build ./
cd ../

# Installing the packages as python packages (do not change the ordering)
python -m pip install -e ./GantryMQ
python -m pip install -e ./sipmpdf
python -m pip install -e ./SiPMCalibControl
```

Here you should be able to run the various programs provided in the 

## Contributing to the code

The main code base is hosted at this [GitHub repository][github]. Contact the
developers for the pull request if you have something you want to add into the
code base!

### Code organization

Documentations for control software development can be found in their various
directories:

- Documentation of the Hardware interfaces and other minimal dependency helper
  objects/functions can be found [here](@ref hardware). The `src` directory
  contains the C++ implemented classes, and the `cmod` directory contains the
  python objects along with the python bindings for the C++ classes.
- Documentation of the CLI interface can be found [here](@ref cli_design). Files for
  this is typically found in the `ctlcmd` directory.
- Documentation of the GUI interface can be found [here](@ref gui_design). Files for
  this is typically found in the `server` directory:
  - The server side code is found in the `server/sockets` directory.
  - The client side code is found in the `server/static/js` directory.
  - Styling file will likely not get their own documentation.

[conda]: https://conda.io/projects/conda/en/latest/user-guide/install/index.html
[hardware]: https://github.com/UMDCMS/GantryMQ
