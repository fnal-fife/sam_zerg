#!/bin/sh

# ensure the sam station is properly set up to run
pip install --no-deps --no-cache-dir -e /opt/sam/sam_station/sam-station

# Make the logging directory
mkdir /var/log/sam

bin/sam_station /opt/sam/sam_station/sam_station_config.yaml
#tail -f /dev/null
