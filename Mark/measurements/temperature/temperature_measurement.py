import os
import time
import signal
import sys
from core.logger import Logger
from core.cmd_runner import CommandRunner

ENV_DEVICE_NAME = os.environ.get('PC_NAME', "Mark1")  # should be your rasp name
ENV_MODEM = os.environ.get('MODEM', "Quectel_BG96")  # should be Qualcomm or Quectel
ENV_DURATION = os.environ.get('DURATION')  # should be the number of ping to send
ENV_SLEEP = os.environ.get('SLEEP', 1)  # should be the number of seconds to sleep between measurement

LOGGER = Logger('temperature_measurement', ENV_DEVICE_NAME, ENV_MODEM)


def signal_handler(sigum, frame):
    sys.exit(0)


def run_temperature_measurement():
    """
    Run temperature measurement for a given number of seconds.
    """

    start_time = time.time()
    while True:
        try:
            temperature_output = CommandRunner.run("cat /sys/class/thermal/thermal_zone0/temp")

            # parse temperature output
            temperature = float(temperature_output) / 1000
            LOGGER.log_info(f"{temperature}")

            # wait ENV_SLEEP seconds
            time.sleep(float(ENV_SLEEP))

            if ENV_DURATION is not None and time.time() - start_time > float(ENV_DURATION):
                break
        except Exception as e:
            LOGGER.log_error(f"Error while measuring temperature: {e}")
            break


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

    if not isInteger(ENV_SLEEP) and not isFloat(ENV_SLEEP):
        LOGGER.log_error("Duration and sleep must be a positive number.")
        sys.exit(1)

    run_temperature_measurement()
