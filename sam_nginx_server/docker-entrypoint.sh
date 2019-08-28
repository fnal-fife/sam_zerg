#!/bin/bash

if [ $# -gt 0 ]; then
    exec "$@"
else
    exec nginx -g 'daemon off;'
fi
