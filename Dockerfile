# Primary base image setup
FROM    ubuntu:23.10
WORKDIR /srv

# List of tools to install using standard apt-get
ARG BASE_TOOLS="tar wget gzip xz-utils"
ARG MAKE_TOOLS="g++ libfmt-dev cmake-extras"
ARG PYTHON_TOOLS="python3-dev python3-pybind11 pybind11-dev python3-pip python3-venv"
ARG OPENCV_TOOLS="libopencv-highgui-dev libopencv-dev"
ARG DRS_TOOLS="libwxgtk3.2-dev libusb-1.0-0-dev libusb-dev"
ARG NPM_TOOLS="npm"

# Installing common packages
RUN apt update ;                          \
    apt-get -y install ${BASE_TOOLS} ;    \
    apt-get -y install ${MAKE_TOOLS} ;    \
    apt-get -y install ${PYTHON_TOOLS} ;  \
    apt-get -y install ${OPENCV_TOOLS} ;  \
    apt-get -y install ${DRS_TOOLS} ;     \
    apt-get -y install ${NPM_TOOLS} ;

RUN mkdir -p /opt/external

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
#     mv  opt/picoscope /opt/external/picoscope ;                                                        \
#     rm -rf control.tar.gz debian-binary;                                                               \

### External packages -- DRS4
RUN wget https://www.psi.ch/sites/default/files/import/drs/SoftwareDownloadEN/drs-5.0.5.tar.gz ; \
    tar zxvf drs-5.0.5.tar.gz;                                                                   \
    mv drs-5.0.5/ /opt/external/drs;

## Installing python components (using pip to pin version if needed).
ENV  VIRTUAL_ENV=/opt/venv
ENV  PATH="$VIRTUAL_ENV/bin/:$PATH"
COPY ./requirements.txt ./requirements.txt
RUN  python3 -m venv --system-site-packages $VIRTUAL_ENV; \
     pip install -r requirements.txt

# TODO: installing the external javascript dependencies here
RUN npm install -g sass
