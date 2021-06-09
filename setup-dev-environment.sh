#!/bin/bash

export DOCKER_BUILDKIT=1
export SAM_WEB_HOST=localhost
export EXPERIMENT=sam_bjwhite
pushd .
gosamclient
. setup_sam_client
popd
