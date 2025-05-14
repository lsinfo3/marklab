# this script is used to perform traceroute measurements to one or more destinations
import os
from core.cmd_runner import CommandRunner
from core.logger import Logger

ENV_DEVICE_NAME = os.environ.get('PC_NAME')  # should be your rasp name
ENV_MODEM = os.environ.get('MODEM')
ENV_INTERFACE = os.environ.get('INTERFACE')  # should be the interface of the modem
ENV_PARAM = os.environ.get('PARAM', "")  # should be the parameter to use
ENV_DESTINATIONS = os.environ.get('DEST', '8.8.8.8')  # should be the destination ip address to ping or check


# init logger
LOGGER = Logger('traceroute_measurement', ENV_DEVICE_NAME, ENV_MODEM)


def run_traceroute_measurement():
    try:
        LOGGER.log_info(f"Running traceroute measurement on {ENV_INTERFACE} with target {ENV_DESTINATIONS} and param {ENV_PARAM}")
        traceroute_output = CommandRunner.run(f"traceroute -i {ENV_INTERFACE} {ENV_PARAM} {ENV_DESTINATIONS}")

        print(traceroute_output)

    except Exception as e:
        LOGGER.log_error(f"Error: {str(e)}")


if __name__ == '__main__':
    if ENV_DEVICE_NAME is None or ENV_INTERFACE is None:
        LOGGER.log_error("Error: DEVICE_NAME and INTERFACE must be set")
        exit(1)

    if ENV_DESTINATIONS is None or ENV_DESTINATIONS == "" or ENV_DESTINATIONS.isspace():
        LOGGER.log_error("Error: DEST must be set")
        exit(1)

    if ENV_DESTINATIONS.__contains__(";"):
        destinations = ENV_DESTINATIONS.split(";")
        for dest in destinations:
            ENV_DESTINATIONS = dest
            run_traceroute_measurement()
    else:
        run_traceroute_measurement()

