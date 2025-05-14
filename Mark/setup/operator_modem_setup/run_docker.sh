#!/bin/bash

docker run -it -e PC_NAME=Mark-1 -e MODEM=Quectel_EC21 -e PORT=/dev/ttyUSB6 -e CONNECT_OPERATOR=RANDOM -e ACCESS_TECH=7 -v /var/run/dbus:/var/run/dbus -v /run/udev:/run/udev:ro -v /dev/bus/usb:/dev/bus/usb --network host --privileged setup-operator-modem