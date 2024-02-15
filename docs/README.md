# Development manual

## Setting up the development environment

This manual assuming a UNIX-like system with [`conda`][conda] available, as
this will be used to set up the other requirements of the system independent of
the developer system. Once you have `conda` available, you can install
everything that is needed using the following commands:

```bash
# Getting the custom code to you working directory
git clone https://github.com/UMDCMS/SiPMCalibControl
git clone https://github.com/UMDCMS/GantryMQ/

# Setting up the conda environment without the custom code base just yet
conda env create --file ./environment.yml

# Starting up the conda environment
conda activate gantry_control

# Compiling the custom code for interacting with n-tuples
cd SiPMCalibControl
cmake ./ && cmake --build ./
cd ..

# Installing the control software python to the environment, must be in this order
python -m pip install -e ./GantryMQ
python -m pip install -e ./SiPMCalibControl
```

To test that this can

[conda]: https://conda.io/projects/conda/en/latest/user-guide/install/index.html
