#!/bin/bash

# Starting up the fast control, data pulling and slow control servers on the
# tileboard tester. Notice that the 3 servers will be pushed to be a background
# process with all outputs discarded (we assume that the 3 servers loaded on the
# tileboard are production ready). So this script will only output three
# numbers: the PID of the 3 servers.


# Starting the fast servers
source /opt/hexactrl/ROCv2/env.sh
cd ~/sw/hexactrl-sw/
/opt/hexactrl/ROCv2/bin/zmq-server > /dev/null 2>&1 &
/opt/hexactrl/ROCv2/bin/zmq-client > /dev/null 2>&1 &

# Starting the slow server
cd /home/HGCAL_dev/sw/hexactrl-sw/zmq_i2c/gbt-sca-sw/
source env.sh
export PYTHONPATH=$PYTHONPATH:$HOME/sw/hgc-engine-tools
cd /home/HGCAL_dev/sw/hexactrl-sw/zmq_i2c
python3 /home/HGCAL_dev/sw/hexactrl-sw/zmq_i2c/zmq_server.py > /dev/null 2>&1 &
