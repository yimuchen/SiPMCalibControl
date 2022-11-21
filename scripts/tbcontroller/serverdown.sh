#!/bin/bash

# Closing the fast control, data pulling and slow control server on the
# tileboard tester. We are assuming that the servers were started using the
# serverup.sh script
kill $(ps aux | grep 'zmq-server' | grep -v grep | awk '{print $2}')
kill $(ps aux | grep 'zmq-client' | grep -v grep | awk '{print $2}')
kill $(ps aux | grep 'zmq_server' | grep -v grep | awk '{print $2}')
