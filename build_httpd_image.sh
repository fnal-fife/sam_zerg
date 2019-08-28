#!/bin/bash

if [[ -z $NO_CACHE_DOCKER_BUILD ]]; then
    docker build -t sam_httpd_server sam_httpd_server 
else
    docker build --no-cache -t sam_httpd_server sam_httpd_server 
fi
