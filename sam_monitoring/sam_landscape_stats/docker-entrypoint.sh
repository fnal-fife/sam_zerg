#!/bin/bash

while [ 1 ]
do
   #/sam_stats_graphite.py fifemondata.fnal.gov:2004 file:db_read_password >& /tmp/graphite_stats.out  
   #/sam_stats_graphite.py fifemondata.fnal.gov:2004 file:db_read_password

    # GRAPHITE_SERVER_HOST/PORT: Tell the data where to go
    # PASSWORD_FILE: Path to the password file. Make sure to mount this in off the Docker host
    /sam_stats_graphite.py $GRAPHITE_SERVER_HOST:$GRAPHITE_SERVER_PORT $PASSWORD_FILE
    sleep 300
done
