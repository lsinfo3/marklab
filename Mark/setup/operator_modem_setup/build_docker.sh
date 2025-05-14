#!/bin/bash

# Move into the directory containing the Dockerfile
cd "$(dirname "$0")"

cd ../../

# Build the docker image
docker build -t setup-operator-modem -f ./setup/operator_modem_setup/Dockerfile .

