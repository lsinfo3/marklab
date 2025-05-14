import requests

from time import sleep

import sys
sys.path.append("/home/ubuntu/mark")

from core.utils_api import API_URL, REQUEST_HEADERS, REQUEST_TIMEOUT
from helper.tinkerforge.ip_connection import IPConnection

import dotenv


HOST = "localhost"
PORT = 4223


# Print incoming enumeration
def cb_enumerate(uid, connected_uid, position, hardware_version, firmware_version,
                 device_identifier, enumeration_type):
    if enumeration_type == IPConnection.ENUMERATION_TYPE_DISCONNECTED:
        return
    device = None
    if position == "a":
        device = "Raspberry_Pi"
    elif position == "b":
        device = "Quectel_EC21"
    elif position == "c":
        device = "GPS"
    elif position == "d":
        device = "Quectel_BG96"


    # if device is not in the database, insert it

    if device == "Raspberry_Pi" or device == "Quectel_BG96" or device == "Quectel_EC21":
        response = requests.post(f"{API_URL}/tinkerforge/", headers=REQUEST_HEADERS, verify=False, timeout=REQUEST_TIMEOUT, json={
            "device": device,
            "uid": uid
        })
        response.raise_for_status()
    elif device == "GPS":
        # if device is gps, update the .env file
        dotenv.set_key(dotenv_path="/home/ubuntu/mark/.env.device", key_to_set="GPS_UID", value_to_set=uid)

    if device is not None:
        print(f"Device {device} added or updated in database or .env.device file.")
    else:
        print(
            f"Device {device} not found in database. Position: {position} UID: {uid}. Please add it to database, if necessary.")


if __name__ == "__main__":
    # Create connection and connect to brickd
    try:
        ipcon = IPConnection()
        ipcon.connect(HOST, PORT)

        # Register Enumerate Callback
        ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE, cb_enumerate)

        # Trigger Enumerate
        ipcon.enumerate()

        # Sleep for 15 seconds until all devices are enumerated/broadcasted.
        sleep(15)
        ipcon.disconnect()
        print("Done")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
