#!/bin/bash
# Start up script for tileboard tester. To be run at the start of cold booting.

# Loading the last loaded firmware into the system (Additional instructions will
# be given should you need to update the firmware)
sudo fw-loader reload

# Setting up permission for user access to I2C controls.
sudo sh $HOME/fw/gpio_i2c_chmod.sh