#!/bin/bash

# Linking external objects to external directory
ln -sf /opt/external/drs /srv/external/drs
# ln -sf /opt/external/picoscope ./external/picoscope

# Compiling C++ related components
CXX=/usr/bin/g++ cmake ./
CXX=/usr/bin/g++ cmake --build ./
