#!/bin/bash

# Move into the directory containing the Dockerfile
cd "$(dirname "$0")"

cd ../../

# Run the docker build command
docker build -t exp-idle -f ./measurements/idle/Dockerfile .