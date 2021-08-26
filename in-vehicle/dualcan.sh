#!/bin/bash

# Seeed 2 Channel Shield Configuration
# $ sudo chmod +x dualcan.sh    # should be done first
# $ ./dualcan.sh    # then do this

sudo ip link set can0 down
sudo ip link set can1 down
sudo ip link set can0 up type can bitrate 250000 restart-ms 1000 fd off
sudo ip link set can1 up type can bitrate 250000 restart-ms 1000 fd off
sudo ifconfig can0 txqueuelen 2000
sudo ifconfig can1 txqueuelen 2000
