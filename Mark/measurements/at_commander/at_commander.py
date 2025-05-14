from core.at_cmds import ATCommands
from core.logger import Logger
import os

ENV_MODEM = os.environ.get('MODEM')
ENV_PORT = os.environ.get('PORT')
ENV_BAUDRATE = os.environ.get('BAUDRATE', 115200)
ENV_TIMEOUT = os.environ.get('TIMEOUT', 600)
ENV_WAIT_TIME = os.environ.get('WAIT_TIME', 600)
ENV_DEVICE_NAME = os.environ.get('PC_NAME')
ENV_COMMAND = os.environ.get('COMMAND')
ENV_REPETITIONS = os.environ.get('REPETITIONS', 1)

# init the logger
logger = Logger('at_commander', ENV_DEVICE_NAME, ENV_MODEM)


def set_error_message(problem, reason):
    logger.log_error(f"{problem}: {reason}")
    exit(1)


def run_at_commander():
    try:
        logger.log_info(f"Start AT command execution: {ENV_COMMAND}")
        for i in range(int(ENV_REPETITIONS)):
            # run the AT command
            response, result = ATCommands.run_command(ENV_PORT, ENV_COMMAND, _baudrate=ENV_BAUDRATE,
                                                      _timeout=ENV_TIMEOUT, _wait_time=ENV_WAIT_TIME)
            if not response:
                set_error_message(f"Error while executing the AT command: {ENV_COMMAND}", result)
            if int(ENV_REPETITIONS) > 1:
                logger.log_info(f"AT command execution {i + 1}/{ENV_REPETITIONS}")
            print(result)
    except Exception as e:
        set_error_message("Error during AT command execution", str(e))


def isInteger(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def main():
    if not ENV_COMMAND:
        set_error_message("Error: Missing environment variable: COMMAND", "")
        exit(1)

    if not isInteger(ENV_REPETITIONS):
        set_error_message("Error: REPETITIONS must be an integer", "")
        exit(1)

    if ENV_COMMAND.__contains__('CFUN') or ENV_COMMAND.__contains__('cfun'):
        set_error_message("Error: CFUN command is not allowed", "")
        exit(1)

    try:
        run_at_commander()
    except Exception as e:
        set_error_message("Error during AT command execution", str(e))
        exit(1)


if __name__ == '__main__':
    main()
