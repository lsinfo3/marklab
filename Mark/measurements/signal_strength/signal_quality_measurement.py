from core.at_cmds import ATCommands
from core.logger import Logger
from time import sleep
import os

ENV_MODEM = os.environ.get('MODEM')
ENV_PORT = os.environ.get('PORT')
ENV_BAUDRATE = os.environ.get('BAUDRATE', 115200)
ENV_TIMEOUT = os.environ.get('TIMEOUT', 30)
ENV_WAIT_TIME = os.environ.get('WAIT_TIME', 120)
ENV_DEVICE_NAME = os.environ.get('PC_NAME')
ENV_REPETITION = os.environ.get('REPETITION', 1)
ENV_SLEEP = os.environ.get('SLEEP', 10)

# init the logger
logger = Logger('signal_strength', ENV_DEVICE_NAME, ENV_MODEM)


def run_signal_strength_measurement():
    try:
        command = "AT+CSQ"
        repetition = int(ENV_REPETITION)
        sleep_time = int(ENV_SLEEP)
        for i in range(repetition):
            # get the signal strength
            status, result = ATCommands.run_command(ENV_PORT, command, _baudrate=ENV_BAUDRATE, _timeout=ENV_TIMEOUT, _wait_time=ENV_WAIT_TIME)
            # log the signal strength
            if status:
                result = result.replace("\r", "")
                result = result.replace("\n", "")
                result = result.replace("OK", "")
                result = result.replace("+CSQ: ", "")
                result = result.split(",")
                rssi = result[0]
                qual = result[1]
                logger.log_info(f"RSSI: {rssi}, QUAL: {qual}")
            if i < repetition - 1:
                sleep(sleep_time)
    except Exception as e:
        logger.log_error(f"Error: {str(e)}")


if __name__ == '__main__':
    if not ENV_MODEM:
        logger.log_error("MODEM is not set")
        exit(1)

    if not ENV_PORT:
        logger.log_error("PORT is not set")
        exit(1)

    if ENV_REPETITION is None:
        logger.log_error("REPETITION is not set")
        exit(1)

    if ENV_SLEEP is None:
        logger.log_error("SLEEP is not set")
        exit(1)

    run_signal_strength_measurement()
    exit(0)
