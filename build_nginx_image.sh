#!/bin/bash

if [[ -z $NO_CACHE_DOCKER_BUILD ]]; then
    docker build -t sam_nginx_server sam_nginx_server 
else
    docker build --no-cache -t sam_nginx_server sam_nginx_server 
fi
