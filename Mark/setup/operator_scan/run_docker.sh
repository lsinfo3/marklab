#!/bin/bash

docker -H ssh://ubuntu@172.16.32.30 run -it --rm -v /var/run/dbus:/var/run/dbus --privileged scan-operator