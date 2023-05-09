FROM archlinux:latest

WORKDIR /tmp/docker

# Installing the required packages for C++ related objects
RUN pacman -Sy --noconfirm "base-devel"
RUN sudo pacman -Sy --noconfirm "cmake" "boost" "opencv" "pybind11"
# Special packages
RUN sudo pacman -Sy --noconfirm "qt5-base" "hdf5-openmpi" "vtk" "glew"

#  Installing python packages
RUN sudo pacman -Sy --noconfirm "python-numpy" "python-scipy" "python-opencv"
RUN sudo pacman -Sy --noconfirm "python-flask-socketio" "python-paramiko"
RUN sudo pacman -Sy --noconfirm "python-pyzmq" "python-yaml" "python-uproot"

# Additional packages
RUN sudo pacman -Sy --noconfirm "npm" "git"

# Getting the external hardware interfaces


## COPY source code into main working directory and start
RUN npm install -g sass
COPY . .
RUN cmake         ./
RUN cmake --build ./

## This docker image is mainly designed for testing the GUI session
CMD python gui_control.py
