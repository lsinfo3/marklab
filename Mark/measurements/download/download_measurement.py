import os
import re

from core.cmd_runner import CommandRunner
from core.logger import Logger
from core.json_logger import JsonLogger
from time import sleep

ENV_DEVICE_NAME = os.environ.get('PC_NAME', "Mark1")  # should be your rasp name
ENV_MODEM = os.environ.get('MODEM', "Quectel_BG96")  # should be Qualcomm or Quectel
ENV_INTERFACE = os.environ.get('INTERFACE', "wwan1")  # should be the interface of the modem
ENV_URL = os.environ.get('URL', "")  # should be the destination ip address to ping or check
ENV_OUTPUT_FORMAT = os.environ.get('OUTPUT_FORMAT', '{"total": %{size_download}, "speed_download": %{speed_download}, "time_total": %{time_total}}')  # should be json or text
ENV_OUTPUT = os.environ.get('OUTPUT', "/dev/null")  # should be the output file
ENV_TIMEOUT = os.environ.get('TIMEOUT', 7200)  # should be the timeout of the modem
ENV_REPETITIONS = os.environ.get('REPETITIONS', 5)  # should be the number of repetitions
ENV_SLEEP = os.environ.get('SLEEP', 1)  # should be the number of seconds to sleep between repetitions
ENV_ARGS = os.environ.get('ARGS', "")  # should be the arguments for the curl command

args = {
    "device_name": ENV_DEVICE_NAME,
    "modem": ENV_MODEM,
    "interface": ENV_INTERFACE,
    "url": ENV_URL,
    "output_format": ENV_OUTPUT_FORMAT,
    "output": ENV_OUTPUT,
    "timeout": ENV_TIMEOUT,
    "repetitions": ENV_REPETITIONS,
    "sleep": ENV_SLEEP,
    "args": ENV_ARGS
}

# init logger
LOGGER = Logger('curl_measurement_detail', ENV_DEVICE_NAME, ENV_MODEM)
JSON_LOGGER = JsonLogger('curl_measurement', ENV_DEVICE_NAME, ENV_MODEM)

CREDENTIALS_PATTERN = re.compile(r"(-u|--user)\s*\S+")

def run_curl_measurement():
    try:
        LOGGER.log_info(f"Running curl measurement on {ENV_INTERFACE} with target {ENV_URL}")

        global ENV_ARGS

        # For HTTP server add user and password here

        # if ENV_URL.startswith("{Insert download link here}"):
        #    ENV_ARGS += " -u user:password --insecure"

        # Remove credentials from log
        args["args"] = re.sub(CREDENTIALS_PATTERN, r"\1 ***:***", ENV_ARGS)

        curl_command = f"curl -s -o {ENV_OUTPUT} -w '{ENV_OUTPUT_FORMAT}' --interface {ENV_INTERFACE} --max-time {ENV_TIMEOUT} {ENV_ARGS} {ENV_URL}"

        for _ in range(0, int(ENV_REPETITIONS)):
            curl_output = CommandRunner.run(curl_command)

            # hotfix: sometime the cmd runner returns an error, because of
            # due to a suspected timeout from the destination or the modem.
            # In this case, we just take the output of the last line
            if curl_output.__contains__("Error"):
                curl_output = curl_output.split("\n")
                curl_output = curl_output[-1]
                JSON_LOGGER.log_error_json(curl_output, arguments=args)
            else:
                JSON_LOGGER.log_info_json(curl_output, arguments=args)

            sleep(int(ENV_SLEEP))

    except Exception as e:
        LOGGER.log_error(f"Error: {str(e)}")


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
    if ENV_REPETITIONS is not None and not isInteger(ENV_REPETITIONS):
        LOGGER.log_error("Repetitions must be a positive integer.")
        raise ValueError("Repetitions must be a positive integer.")

    if ENV_SLEEP is not None and not isInteger(ENV_SLEEP) and not isFloat(ENV_SLEEP):
        LOGGER.log_error("Sleep must be a positive number.")
        raise ValueError("Sleep must be a positive number.")

    run_curl_measurement()
