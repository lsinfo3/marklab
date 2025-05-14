#!/bin/bash

#get the directory of this script
cd "$(dirname "$0")"

# move to root directory
cd ../../

# build the docker image
docker -H ssh://ubuntu@172.16.32.30 build -t exp-delay-ping -f ./measurements/delay/Dockerfile . --no-cache

