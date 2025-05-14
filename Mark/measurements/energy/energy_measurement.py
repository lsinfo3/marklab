#!/usr/bin/env python
import os

from helper.tinkerforge.ip_connection import IPConnection
from helper.tinkerforge.bricklet_voltage_current_v2 import BrickletVoltageCurrentV2
from timeit import default_timer as timer
import numpy as np
import pandas as pd
import pyarrow.feather as feather
import time
import signal
import sys

HOST = os.environ.get("HOST", "localhost")
PORT = os.environ.get("PORT", 4223)
UID = os.environ.get("UID", "U4i")

# After how many samples should a log be written to disk
log_rotation_at = 10000

# What iteration time are we aiming for?
# This is the time between two samples.
# This needs to be in line with averaging length and conversion times of the vc bricklet.
target_iteration_time = 0.005

# Initialize empty dataframe used for vector storage and efficient writing to disk
df_data = pd.DataFrame()

# Pre-initialize vectors to store monitoring data
vec_iteration_time = np.zeros(log_rotation_at)
vec_epoch = np.zeros(log_rotation_at)
vec_current = np.zeros(log_rotation_at)
vec_voltage = np.zeros(log_rotation_at)

log_path = "./exp-bricklet-voltage-current/logs"


# Get current epoch time in milliseconds
def current_milli_time():
    return round(time.time() * 1000)


def signal_handler(sigum, frame):
    global df_data
    print("Stopping measurement...")

    df_data["epoch"] = vec_epoch
    df_data["diff"] = vec_iteration_time
    df_data["current"] = vec_current
    df_data["voltage"] = vec_voltage

    # remove unused rows
    df_data = df_data[:i % log_rotation_at]
    feather.write_feather(df_data, f"{log_path}/data_{int(time.time())}.feather")

    print("Done. Exiting...")
    ipcon.disconnect()
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Create IP connection
    ipcon = IPConnection()

    # Create device object
    vc = BrickletVoltageCurrentV2(UID, ipcon)

    # Connect to brickd
    ipcon.connect(HOST, PORT)

    # !! Don't use device before ipcon is connected !!

    # Set averaging length and conversion times
    vc.set_configuration(1, 4, 4)

    i = 0
    # Perform sampling

    while True:
        start = timer()

        if i % log_rotation_at == 0 and i != 0:  # TODO: maybe remove i != 0 condition if it messes with runtime (seems to be working for now)
            df_data["epoch"] = vec_epoch
            df_data["diff"] = vec_iteration_time
            df_data["current"] = vec_current
            df_data["voltage"] = vec_voltage
            feather.write_feather(df_data, f"{log_path}/data_{int(time.time())}.feather")

        # Get current voltage
        vec_voltage[i % log_rotation_at] = vc.get_voltage()
        # Get current current
        vec_current[i % log_rotation_at] = vc.get_current()
        # Get current timestamp
        vec_epoch[i % log_rotation_at] = current_milli_time()

        end = timer()
        while (end - start) < target_iteration_time:
            end = timer()

        # Get time since last iteration
        vec_iteration_time[i % log_rotation_at] = (end - start)
        i = i + 1