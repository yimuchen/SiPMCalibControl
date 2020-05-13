FROM archlinux:latest

WORKDIR /tmp/docker

RUN pacman -Sy --noconfirm "base-devel"
RUN sudo pacman -Sy --noconfirm "cmake" "boost" "opencv"
RUN sudo pacman -Sy --noconfirm "python-numpy" "python-scipy"
RUN sudo pacman -Sy --noconfirm "python-flask-socketio" "python-paramiko"
RUN sudo pacman -Sy --noconfirm "npm" "git"
RUN sudo pacman -Sy --noconfirm "qt5-base" "hdf5-openmpi" "vtk" "glew"

## Temporary user for building the picoscope library
RUN useradd --no-create-home --shell=/bin/bash build
RUN usermod -L build
RUN echo "build ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
USER build

## Installing libps5000 stuff from AUR
RUN sudo git clone https://aur.archlinux.org/libps5000.git
RUN sudo chmod 777 libps5000
RUN cd libps5000 && makepkg -s && sudo pacman -U --noconfirm libps5000*.pkg.*

## Moving back to the ROOT user,
## COPY source Code into main working directory and start
USER root
RUN npm install -g sass
COPY . .
RUN cmake         ./
RUN cmake --build ./

## This docker image is mainly designed for testing the GUI session
CMD python gui_control.py
