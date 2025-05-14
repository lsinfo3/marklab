#!/bin/bash

# Move into the directory containing the Dockerfile
cd "$(dirname "$0")"

cd ../../

# Run the docker build command
docker -H ssh://ubuntu@172.16.32.30 build -t exp-temperature -f ./measurements/temperature/Dockerfile . --no-cache