#!/bin/bash

# Move into the directory containing the Dockerfile
cd "$(dirname "$0")"

cd ../../

# Build the docker image
docker build -t setup-modem-act -f ./setup/modem_act_setup/Dockerfile .