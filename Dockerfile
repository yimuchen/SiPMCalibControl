# Primary base image setup
FROM    ubuntu:23.10
WORKDIR /srv

# Common linux tools
RUN apt update ;                                       \
    apt-get -y install "tar" "wget" "gzip" "xz-utils"

# Linux libraries required for C/C++ components
RUN apt-get -y install "g++" "libfmt-dev" "cmake-extras"               \
                       "python3-dev" "python3-pybind11" "pybind11-dev" \
                       "libopencv-highgui-dev" "libopencv-dev"

RUN mkdir ./external

### External packages -- picoscope

# TODO: currenly picoscope only supports ARMv7. We shall not use ARMv7, as this
# makes python package management very difficult (neither pip nor conda ships
# with pre-compiled python packages on ARMv7, and archlinux-arm is the only
# known distribution to come with precompiled python-awkward). So the picoscope
# interface will be disabled until either PicoTech officially supports ARM64 or
# we find a way to easily cross compile on ARMv8.

# RUN wget https://labs.picotech.com/debian/pool/main/libp/libps5000/libps5000_2.1.83-3r3073_amd64.deb ; \
#     ar x libps5000_2.1.83-3r3073_amd64.deb ;                                                           \
#     tar xvf data.tar.xz ;                                                                              \
#     mv  opt/picoscope ./external/picoscope ;                                                           \
#     rm -rf control.tar.gz debian-binary;                                                               \

### External packages -- DRS4
RUN wget https://www.psi.ch/sites/default/files/import/drs/SoftwareDownloadEN/drs-5.0.5.tar.gz ; \
    tar zxvf drs-5.0.5.tar.gz;                                                                   \
    mv drs-5.0.5/ external/drs;                                                                  \
    apt-get -y install "libwxgtk3.2-dev" "libusb-1.0-0-dev" "libusb-dev"

## Installing python components (using pip to pin version if needed).
ENV  VIRTUAL_ENV=/opt/venv
ENV  PATH="$VIRTUAL_ENV/bin/:$PATH"
COPY ./requirements.txt ./requirements.txt
RUN  apt-get -y install "python3-pip" "python3-venv"      \
                        "libssl-dev" "libffi-dev" "curl"; \
     python3 -m venv --system-site-packages $VIRTUAL_ENV; \
     pip install -r requirements.txt

# TODO: installing the external javascript dependencies here
RUN apt-get -y install "npm" ; \
    npm install -g sass

# Copying the C/C++ related repository code
COPY ./src   ./src
COPY ./cmod  ./cmod
COPY ./bin   ./bin

# Running the C/C++ compilation
COPY ./CMakeLists.txt ./CMakeLists.txt
RUN  CXX=/usr/bin/g++ cmake         ./ ; \
     CXX=/usr/bin/g++ cmake --build ./

# Copying the python-only components
COPY ./ctlcmd ./ctlcmd
COPY ./server ./server

# Creating server side objects
RUN sass server/style.scss:style.css ; \
    mv   style.css server/style.css

# Copying the top level control scripts and configurations
COPY ./control.py     ./control.py
COPY ./gui_control.py ./gui_control.py
COPY ./dofiles ./dofiles
COPY ./cfg     ./cfg

# Default is starting an interactive shell
CMD  /bin/bash
