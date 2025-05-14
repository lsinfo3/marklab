# TODO: Is this file depreceated?

import os
import time
import sys
import signal

from core.utils import isInteger, isFloat
from core.logger import Logger
from core.cmd_runner import CommandRunner
from core.mmcli_parser import ModemManagerParser

ENV_DEVICE_NAME = os.environ.get('PC_NAME', "Mark1")  # should be your rasp name
ENV_MODEM = os.environ.get('MODEM', "Quectel_BG96")  # should be Qualcomm or Quectel
ENV_DURATION = os.environ.get('DURATION', 60)  # should be the time to measure the signal strength
ENV_SLEEP = os.environ.get('SLEEP', 5)  # should be the time to sleep between measurements
ENV_REFRESH_RATE = os.environ.get('REFRESH_RATE', 5)  # should be the time to sleep between measurements

LOGGER = Logger('signal_strength_measurement', ENV_DEVICE_NAME, ENV_MODEM)


def signal_handler(sigum, frame):
    sys.exit(0)


def run_signal_strength_measurement():
    try:
        start_time = time.time()
        while True:
            signal_strength_output = CommandRunner.run(f"mmcli -m {ENV_MODEM} --signal-get")
            signal_strength_output = ModemManagerParser.parse_signal_strength(signal_strength_output)
            LOGGER.log_info(f"{signal_strength_output} \n")

            if ENV_DURATION is not None and time.time() - start_time > float(ENV_DURATION):
                break

            time.sleep(int(ENV_SLEEP))
    except Exception as e:
        LOGGER.log_error(f"Error: {str(e)} \n")


def setup_signal_strength_rate():
    try:
        signal_strength_output = CommandRunner.run(f"mmcli -m {ENV_MODEM} --signal-setup={ENV_REFRESH_RATE}")
        LOGGER.log_info(f"Signal strength rate set to {ENV_REFRESH_RATE} seconds. Output: {signal_strength_output} \n")
        return True
    except Exception as e:
        LOGGER.log_error(f"Error: {str(e)} \n")
        return False


if __name__ == '__main__':

    signal.signal(signal.SIGINT, signal_handler)

    if not ENV_MODEM:
        LOGGER.log_error("MODEM is not set")
        exit(1)

    if ENV_DURATION is not None and not isInteger(ENV_DURATION) and not isFloat(ENV_DURATION):
        LOGGER.log_error("Duration must be a positive number.")
        sys.exit(1)

    if not isInteger(ENV_SLEEP) and not isFloat(ENV_SLEEP):
        LOGGER.log_error("Duration and sleep must be a positive number.")
        sys.exit(1)

    ss_setup = setup_signal_strength_rate()
    if ss_setup:
        run_signal_strength_measurement()
    else:
        LOGGER.log_error("Signal strength rate setup failed.")
        sys.exit(1)
