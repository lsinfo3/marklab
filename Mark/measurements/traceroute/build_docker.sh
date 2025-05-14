#!/bin/bash

# Move into the directory containing the Dockerfile
cd "$(dirname "$0")"

cd ../../

# Run the docker build command
docker build -t exp-route-traceroute -f ./measurements/traceroute/Dockerfile . --no-cache