FROM archlinux:latest

WORKDIR /tmp/docker

RUN pacman -Sy --noconfirm "base-devel"
# WORKDIR /tmp/docker
RUN useradd --no-create-home --shell=/bin/bash build
RUN usermod -L build
RUN echo "build ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
USER build

RUN sudo pacman -Sy --noconfirm "cmake" "boost" "opencv"
RUN sudo pacman -Sy --noconfirm "python-numpy" "python-scipy"
RUN sudo pacman -Sy --noconfirm "python-flask-socketio" "python-paramiko"
RUN sudo pacman -Sy --noconfirm "npm" "git"

## Installing libps5000 stuff from AUR
RUN sudo git clone https://aur.archlinux.org/libps5000.git
RUN sudo chmod 777 libps5000
RUN cd libps5000 && makepkg -s && sudo pacman -U --noconfirm libps5000*.pkg.*
#RUN pacman -U --noconfirm *.tar.*

## COPY SOURCE Code into main working directory and start
USER root
RUN npm install -g sass
RUN pacman -Sy --noconfirm "qt5-base" "hdf5-openmpi" "vtk" "glew"
COPY . .
RUN cmake         ./
RUN cmake --build ./

CMD python gui_control.py
