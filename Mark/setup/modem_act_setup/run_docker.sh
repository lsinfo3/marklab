#!/bin/bash

docker run -it --rm -v /var/run/dbus:/var/run/dbus -v /run/udev:/run/udev:ro -v /dev/bus/usb:/dev/bus/usb --privileged setup-modem-act