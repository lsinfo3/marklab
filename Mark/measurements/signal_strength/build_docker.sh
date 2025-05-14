#!/bin/bash

cd "$(dirname "$0")"

cd ../../

docker build -t exp-signal-strength -f ./measurements/signal_strength/Dockerfile . --no-cache