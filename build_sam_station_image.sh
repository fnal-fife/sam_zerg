#!/bin/bash

if [[ -z $NO_CACHE_DOCKER_BUILD ]]; then
    docker build -t sam_station sam_station 
else
    docker build --no-cache -t sam_station sam_station 
fi
