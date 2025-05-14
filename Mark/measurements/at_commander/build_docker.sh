#!/bin/bash

#get the directory of this script
cd "$(dirname "$0")"

# move to root directory
cd ../../

# build the docker image
docker build -t exp-at-commander -f ./measurements/at_commander/Dockerfile . --no-cache


