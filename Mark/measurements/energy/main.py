#!/usr/bin/env python

from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_voltage_current_v2 import BrickletVoltageCurrentV2
from timeit import default_timer as timer
import time
import numpy as np
import pandas as pd
import pyarrow.feather as feather
from os import mkdir

HOST = "localhost"
PORT = 4223
UID = "21hK"

# Name of the measurement scenario
#scenario_name = "arduino_auth_and gprsAttach_5ms/"
scenario_name = "arduino_get_1K_5ms/"
target_folder = "./data/" + scenario_name

# Number of samples to take
#n_samples = 240000
n_samples = 72000

# After how many samples should a log be written to disk
log_rotation_at = 10000

# What iteration time are we aiming for?
# This is the time between two samples.
# This needs to be in line with averaging length and conversion times of the vc bricklet.
target_iteration_time = 0.005

# Initialize empty dataframe used for vector storage and efficient writing to disk
df_data = pd.DataFrame()

# Pre-initialize vectors to store montitoring data
vec_iteration_time = np.zeros(log_rotation_at)
vec_epoch = np.zeros(log_rotation_at)
vec_current = np.zeros(log_rotation_at)
vec_voltage = np.zeros(log_rotation_at)

# Get current epoch time in milliseconds
def current_milli_time():
    return round(time.time() * 1000)

if __name__ == "__main__":

    # Prepare scenario destination folder
    mkdir(target_folder)

    # Create IP connection
    ipcon = IPConnection()

    # Create device object
    vc = BrickletVoltageCurrentV2(UID, ipcon)

    # Connect to brickd
    ipcon.connect(HOST, PORT) 

    # !! Don't use device before ipcon is connected !!

     # Set averaging length and conversion times
    vc.set_configuration(1, 4, 4)

    # Perform sampling
    for i in range(n_samples):

        start = timer()

        if i % log_rotation_at == 0 and i != 0: # TODO: maybe remove i != 0 condition if it messes with runtime (seems to be working for now)
            df_data["epoch"] = vec_epoch
            df_data["diff"] = vec_iteration_time
            df_data["current"] = vec_current
            df_data["voltage"] = vec_voltage
            feather.write_feather(df_data, target_folder + "data_" + str(i) + ".feather")

        # Get current voltage
        vec_voltage[i % log_rotation_at] = vc.get_voltage()
        # Get current current
        vec_current[i % log_rotation_at] = vc.get_current()
        # Get current timestamp
        vec_epoch[i % log_rotation_at] = current_milli_time()

        end = timer()
        while (end-start) < target_iteration_time:
            end = timer()

        # Get time since last iteration
        vec_iteration_time[i % log_rotation_at] = (end - start)

    # Write last iteration to file
    df_data["epoch"] = vec_epoch
    df_data["diff"] = vec_iteration_time
    df_data["current"] = vec_current
    df_data["voltage"] = vec_voltage
    feather.write_feather(df_data, target_folder + "data_" + str(i) + ".feather")

    ipcon.disconnect()