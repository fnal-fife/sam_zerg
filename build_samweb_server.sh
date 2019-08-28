#!/bin/bash

if [[ -z $NO_CACHE_DOCKER_BUILD ]]; then
    docker build -t samweb_server samweb_server 
else
    docker build --no-cache -t samweb_server samweb_server 
fi
