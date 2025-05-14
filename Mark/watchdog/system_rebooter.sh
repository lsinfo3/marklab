#!/bin/bash
# reboot system if job_running is not running
# this script is called every day at 3:00 am

log_file="/home/ubuntu/mark/watchdog/log/system_rebooter.log"

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <name_of_script>"
    echo "$(date +"%Y%m%d%H%M%S") - Error: $0 <name_of_script>" >> "$log_file"
    exit 1
fi

SCRIPT_NAME=$1

# check if job_running is running
if pgrep -af "python" | grep -q "$SCRIPT_NAME"; then

    sleep 120 # wait 2 minutes

    # try again
    if pgrep -af "python" | grep -q "$SCRIPT_NAME"; then
      echo "$(date +"%Y%m%d%H%M%S") - Job $SCRIPT_NAME is running" >> "$log_file"
    else
      echo "$(date +"%Y%m%d%H%M%S") - Job $SCRIPT_NAME is not running" >> "$log_file"
      echo "$(date +"%Y%m%d%H%M%S") - Rebooting system" >> "$log_file"
      reboot
    fi

else
    echo "$(date +"%Y%m%d%H%M%S") - Job $SCRIPT_NAME is not running" >> "$log_file"
    echo "$(date +"%Y%m%d%H%M%S") - Rebooting system" >> "$log_file"
    reboot
fi