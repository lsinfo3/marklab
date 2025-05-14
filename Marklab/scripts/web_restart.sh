#!/bin/bash

docker compose up --build --detach marklab-web
docker compose restart marklab_proxy
