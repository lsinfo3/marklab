#!/bin/bash

# Move into the directory containing the Dockerfile
cd "$(dirname "$0")"

cd ../../

# Build the docker image
docker build -t scan-operator -f ./setup/operator_scan/Dockerfile .
