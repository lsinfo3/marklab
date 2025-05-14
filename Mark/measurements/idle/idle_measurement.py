import os
import time
import signal
import sys
from core.logger import Logger

ENV_DEVICE_NAME = os.environ.get('PC_NAME', "Mark1")  # should be your rasp name
ENV_MODEM = os.environ.get('MODEM', "Quectel_BG96")  # should be Qualcomm or Quectel
ENV_DURATION = os.environ.get('DURATION', 86400)  # 24 hours


LOGGER = Logger('idle_measurement', ENV_DEVICE_NAME, ENV_MODEM)


def signal_handler(sigum, frame):
    sys.exit(0)


def run_idle_measurement():
    """
    Sleep for a given number of seconds.
    """
    LOGGER.log_info(f"Starting idle measurement for {ENV_DURATION} seconds.")
    time.sleep(ENV_DURATION)
    LOGGER.log_info(f"Idle measurement finished after {ENV_DURATION} seconds.")


def isInteger(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def isFloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


if __name__ == '__main__':
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)

    if ENV_DURATION is not None and not isInteger(ENV_DURATION) and not isFloat(ENV_DURATION):
        LOGGER.log_error("Duration must be a positive number.")
        sys.exit(1)
    ENV_DURATION = int(ENV_DURATION)
    run_idle_measurement()
