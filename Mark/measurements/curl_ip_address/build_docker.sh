#!/bin/bash

# Move into the directory containing the Dockerfile
cd "$(dirname "$0")"

cd ../../

# Run the docker build command
docker build -t get-ip-address -f ./measurements/curl_ip_address/Dockerfile . --no-cache