from core.cmd_runner import CommandRunner
from core.logger import Logger
import os

ENV_INTERFACE = os.environ.get('INTERFACE')  # Network interface for hping3
ENV_IP_TARGET = os.environ.get('IP_TARGET', "8.8.8.8")  # Target IP addresses
ENV_DEVICE_NAME = os.environ.get('PC_NAME')  # Device name
ENV_MODEM = os.environ.get('MODEM')  # Modem type
ENV_PARAM = os.environ.get('PARAM', "-S -p 80 -c 60")  # Additional hping3 parameters

LOGGER = Logger('hping_measurement', ENV_DEVICE_NAME, ENV_MODEM)


def run_hping_measurement():
    try:
        LOGGER.log_info(f"Start hping3 measurement to {ENV_IP_TARGET}. Parameters: {ENV_PARAM}")
        # Construct the hping3 command
        hping3_cmd = f"hping3 {ENV_PARAM} -I {ENV_INTERFACE} {ENV_IP_TARGET}"
        hping_output = CommandRunner.run(hping3_cmd)

        print(hping_output)

    except Exception as e:
        LOGGER.log_error(f"Error: {str(e)} \n")


def main():
    if not ENV_INTERFACE:
        LOGGER.log_error("Error: Missing environment variable: INTERFACE")
        exit(1)

    if not ENV_IP_TARGET:
        LOGGER.log_error("Error: Missing environment variable: IP_TARGETS")
        exit(1)

    try:
        run_hping_measurement()
    except Exception as e:
        LOGGER.log_error(f"Error during hping3 measurement: {str(e)} \n")
        exit(1)


if __name__ == '__main__':
    main()
