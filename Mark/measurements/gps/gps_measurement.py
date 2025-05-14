import datetime
import sys
import signal
import time
import os

from core.utils import isInteger, isFloat
from core.logger import Logger
from helper.tinkerforge.ip_connection import IPConnection
from helper.tinkerforge.bricklet_gps_v3 import BrickletGPSV3

HOST = os.environ.get("HOST", "localhost")
PORT = os.environ.get("PORT", 4223)
UID = os.environ.get("UID")
ENV_SLEEP = os.environ.get("SLEEP", 10)
ENV_DEVICE_NAME = os.environ.get("PC_NAME", "Mark1")
ENV_MODEM = os.environ.get('MODEM', "Quectel_BG96")  # should be Qualcomm or Quectel
ENV_DURATION = os.environ.get("DURATION")

LOGGER = Logger("gps_measurement", ENV_DEVICE_NAME, ENV_MODEM)


def signal_handler(sigum, frame):
    sys.exit(0)


def measure_gps():

    # Create IP connection
    ipcon = IPConnection()

    # Create device object
    gps = BrickletGPSV3(UID, ipcon)

    # Connect to brickd
    ipcon.connect(HOST, PORT)

    start_time = time.time()
    while True:
        try:
            # Get current coordinates

            status = gps.get_status()

            if status == 0:         # 0 stands for no fix
                LOGGER.log_error(f"GPS signal not found")
                time.sleep(int(ENV_SLEEP))
                continue

            latitude, ns, longitude, ew = gps.get_coordinates()
            date = gps.get_date_time()

            LOGGER.log_info(f"{datetime.datetime.now()},{latitude},{longitude},{ns},{ew},{date}")
            # wait x second
            time.sleep(int(ENV_SLEEP))

            if ENV_DURATION is not None and time.time() - start_time > float(ENV_DURATION):
                break
        except Exception as e:
            LOGGER.log_error(f"Error while measuring GPS: {e}")
            break

    # Disconnect from brickd
    ipcon.disconnect()


if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)

    if ENV_DURATION is not None and not isInteger(ENV_DURATION) and not isFloat(ENV_DURATION):
        LOGGER.log_error("Duration must be a positive number.")
        sys.exit(1)

    if not isInteger(ENV_SLEEP) and not isFloat(ENV_SLEEP):
        LOGGER.log_error("Duration and sleep must be a positive number.")
        sys.exit(1)

    if UID is None:
        LOGGER.log_error(f"Error: UID is not set! \n")
        exit(1)
    try:
        measure_gps()
    except Exception as e:
        LOGGER.log_error(f"Error: {str(e)} \n")
        sys.exit(1)
