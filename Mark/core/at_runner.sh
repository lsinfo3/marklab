#!/bin/bash

log_file="/home/ubuntu/mark/core/at_runner.log"

# Überprüfen, ob der Parameter übergeben wurde
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <device> <at-command>"
    echo "$(date +"%Y-%m-%d %H:%M:%S") - Error: $0 <device> <at-command>" >> "$log_file"
    exit 1
fi

# Überprüfen, ob das Gerät existiert
if [ ! -c "$1" ]; then
    echo "Device $1 does not exist"
    echo "$(date +"%Y-%m-%d %H:%M:%S") - Error: Device $1 does not exist" >> "$log_file"
    exit 1
fi

device=$1
at_command=$2

# Sende AT-Befehl an das Gerät
response=$(echo "$at_command" | socat - "$device",crnl)

sleep 10   # Warte 10 Sekunden auf die Antwort des Geräts

# Return the response
echo "$response"
echo "$(date +"%Y-%m-%d %H:%M:%S") - Response: $response" >> "$log_file"
exit 0