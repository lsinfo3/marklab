#!/bin/bash

#get the directory of this script
cd "$(dirname "$0")"

# move to root directory
cd ../../

# build the docker image
docker build -t exp-position-gps -f ./measurements/gps/Dockerfile . --no-cache