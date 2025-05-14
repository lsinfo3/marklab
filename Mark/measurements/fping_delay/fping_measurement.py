from core.cmd_runner import CommandRunner
from core.logger import Logger
import os

ENV_INTERFACE = os.environ.get('INTERFACE')  # should be of initialized modem
ENV_IP_TARGETS = os.environ.get('IP_TARGETS',
                                "8.8.8.8")  # should be the destination ip address to ping or check. you can use multiple ip addresses separated by whitespace
ENV_DEVICE_NAME = os.environ.get('PC_NAME')  # should be your rasp name
ENV_MODEM = os.environ.get('MODEM')  # should be Quectel_BG96 or Quectel_EC21
ENV_PARAM = os.environ.get('PARAM', "-c 60")  # should be the parameter for the fping command

# init logger
LOGGER = Logger('fping_measurement', ENV_DEVICE_NAME, ENV_MODEM)


def run_fping_measurement():
    try:
        LOGGER.log_info(
            f"Start fping measurement on {ENV_INTERFACE} interface to {ENV_IP_TARGETS}. Parameters: {ENV_PARAM}")
        # Run the fping command and capture the output
        fping_output = CommandRunner.run(f"fping -D {ENV_PARAM} -I {ENV_INTERFACE} {ENV_IP_TARGETS}")

        print(fping_output)

    except Exception as e:
        LOGGER.log_error(f"Error: {str(e)} \n")


def main():
    if ENV_INTERFACE is None or ENV_INTERFACE == "":
        LOGGER.log_error("Error: Missing environment variables: INTERFACE")
        exit(1)

    if ENV_IP_TARGETS is None or ENV_IP_TARGETS == "":
        LOGGER.log_error("Error: Missing environment variables: IP_TARGETS")
        exit(1)

    try:
        run_fping_measurement()
    except Exception as e:
        LOGGER.log_error(f"Error: {str(e)} \n")
        exit(1)


if __name__ == '__main__':
    main()
