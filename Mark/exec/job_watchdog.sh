#!/bin/bash

DOCKER_CLEANUP_SCRIPT_NAME="../watchdog/docker_cleanup.py"
SYSTEM_CHECK_SCRIPT_NAME="../watchdog/system_watchdog.py"
MODEM_CONTROL_SCRIPT_NAME="../watchdog/modem_control.sh"
SCRIPT_NAME="job_runner.py"

# Function to check script execution status
check_script_status() {
    if pgrep -f "$SCRIPT_NAME" > /dev/null; then
        echo "Script is running."
        return 0  # Script is running
    else
        echo "Script is not running."
        return 1  # Script is not running
    fi
}

# Check if the main script is running
if check_script_status; then
    # Main script is running, do nothing
    echo "Main script is already running. Exiting."
else
    # Main script is not running, execute Docker cleanup script and system watchdog script
    if python3 "$DOCKER_CLEANUP_SCRIPT_NAME"; then
        echo "Docker cleanup script executed successfully."
    else
        echo "Docker cleanup script failed with an exception."
    fi

    if python3 "$SYSTEM_CHECK_SCRIPT_NAME"; then
        echo "System watchdog script executed successfully."
    else
        echo "System watchdog script failed with an exception."
    fi

    # Check if the modem is connected
#    if bash "$MODEM_CONTROL_SCRIPT_NAME" "/dev/ttyUSB8" "AT+CFUN=0"; then
#        echo "Modem deactivated successfully."
#    else
#        echo "Modem deactivation failed with an exception."
#    fi

    # Run the main script
    echo "Restarting the main script..."
    # run the script in the background
    nohup python3 "$SCRIPT_NAME" > /dev/null 2>&1 &
    echo "Main script restarted."
fi
