#!/bin/bash

# Move into the directory containing the Dockerfile
cd "$(dirname "$0")"

cd ../../

docker -H ssh://ubuntu@172.16.32.30 build -t setup-controller-modem -f ./setup/modem_controller/Dockerfile .