FROM archlinux:latest

WORKDIR /srv

# Installing the required packages for C++ related objects
RUN pacman -Sy --noconfirm "base-devel"
RUN pacman -Sy --noconfirm "cmake" "boost" "opencv" "pybind11" "fmt"
# Additional dependencies for external interface
RUN pacman -Sy --noconfirm "qt5-base" "hdf5-openmpi" "vtk" "glew"
RUN pacman -Sy --noconfirm "wxwidgets-gtk3" "libusb-compat"

#  Installing python packages
RUN pacman -Sy --noconfirm "python-setuptools" "python-tqdm"
RUN pacman -Sy --noconfirm "python-numpy" "python-scipy" "python-opencv"
RUN pacman -Sy --noconfirm "python-flask-socketio" "python-paramiko"
RUN pacman -Sy --noconfirm "python-pyzmq" "python-yaml" "python-uproot"

# Additional packages for package management
RUN pacman -Sy --noconfirm "npm" "git" "wget" "tar"
RUN npm install -g sass

## COPY source code into main working directory
# Copying in pieces to avoid re-compiling when minor packages are give
# C++ related objects
COPY ./external ./external

# Getting the external packages picoscope
RUN wget https://labs.picotech.com/debian/pool/main/libp/libps5000/libps5000_2.1.83-3r3073_amd64.deb
RUN ar x libps5000_2.1.83-3r3073_amd64.deb
RUN tar xvf data.tar.xz
RUN mv opt/picoscope ./external/picoscope
RUN rm -rf  control.tar.gz debian-binary usr/ opt/

# Getting external packages -- DRS4
RUN wget https://www.psi.ch/sites/default/files/import/drs/SoftwareDownloadEN/drs-5.0.5.tar.gz
RUN tar zxvf drs-5.0.5.tar.gz
RUN mv drs-5.0.5/ external/drs

COPY ./src      ./src
COPY ./cmod     ./cmod
COPY ./bin       ./bin

# Running the compilation
COPY ./CMakeLists.txt ./CMakeLists.txt
RUN cmake         ./
RUN cmake --build ./

# Copying the configuration files
COPY ./dofiles ./dofiles
COPY ./cfg     ./cfg

# Copying the python-only components
COPY ./ctlcmd         ./ctlcmd
COPY ./server         ./server
COPY ./control.py     ./control.py
COPY ./gui_control.py ./gui_control.py

RUN sass server/style.scss:style.css
RUN mv   style.css server/style.css

## This docker image is mainly designed for testing the GUI session
CMD /bin/bash
