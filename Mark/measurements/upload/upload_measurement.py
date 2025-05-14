import os
import re

from core.cmd_runner import CommandRunner
from core.logger import Logger
from core.json_logger import JsonLogger
from time import sleep

ENV_DEVICE_NAME = os.environ.get('PC_NAME', "Mark1")  # should be your rasp name
ENV_MODEM = os.environ.get('MODEM', "Quectel_BG96")  # should be Qualcomm or Quectel
ENV_INTERFACE = os.environ.get('INTERFACE', "wwan1")  # should be the interface of the modem
ENV_IP_TARGET = os.environ.get('IP_TARGET', "")  # should be the destination ip address to ping or check
ENV_OUTPUT_FORMAT = os.environ.get('OUTPUT_FORMAT', '{"size_upload": %{size_upload}, "average_speed": %{speed_upload}, "time_total": %{time_total}}')  # should be json or text
ENV_FILEPATH = os.environ.get('FILEPATH', "10KB.txt")  # should be the file to upload, e.g. 10KB.txt, 100KB.txt, 1MB.txt, ..
ENV_TIMEOUT = os.environ.get('TIMEOUT', 7200)  # should be the timeout of the modem
ENV_REPETITIONS = os.environ.get('REPETITIONS', 5)  # should be the number of repetitions
ENV_SLEEP = os.environ.get('SLEEP', 1)  # should be the number of seconds to sleep between repetitions
ENV_ARGS = os.environ.get('ARGS', "")  # should be the arguments to pass to the command

args = {
    "device_name": ENV_DEVICE_NAME,
    "modem": ENV_MODEM,
    "interface": ENV_INTERFACE,
    "ip_target": ENV_IP_TARGET,
    "output_format": ENV_OUTPUT_FORMAT,
    "file_path": ENV_FILEPATH,
    "timeout": ENV_TIMEOUT,
    "args": ENV_ARGS
}

# init logger
LOGGER = Logger('upload_measurement_detail', ENV_DEVICE_NAME, ENV_MODEM)
JSON_LOGGER = JsonLogger('upload_measurement', ENV_DEVICE_NAME, ENV_MODEM)

CREDENTIALS_PATTERN = re.compile(r"(-u|--user)\s*\S+")

def run_upload_measurement():
    try:
        LOGGER.log_info(f"Running upload measurement on {ENV_INTERFACE} with target {ENV_IP_TARGET}")

        global ENV_ARGS

        # For HTTP server add user and password here

        # if ENV_URL.startswith("{Insert download link here}"):
        #    ENV_ARGS += " -u user:password --insecure"

        # Remove credentials from log
        args["args"] = re.sub(CREDENTIALS_PATTERN, r"\1 ***:***", ENV_ARGS)

        curl_command = f"curl -F 'file=@./files/{ENV_FILEPATH}' -w '{ENV_OUTPUT_FORMAT}' --interface {ENV_INTERFACE} --max-time {ENV_TIMEOUT} {ENV_ARGS} {ENV_IP_TARGET}"

        for _ in range(0, int(ENV_REPETITIONS)):
            upload_output = CommandRunner.run(curl_command)

            if upload_output.__contains__("Error"):
                upload_output = upload_output.split("\n")
                upload_output = upload_output[-1]
                JSON_LOGGER.log_error_json(upload_output, arguments=args)
            else:
                # get the last line of the output which contains the result
                upload_output = upload_output.split("\n")
                upload_output = upload_output[-1]
                JSON_LOGGER.log_info_json(upload_output, arguments=args)

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
        raise ValueError("REPETITIONS must be an integer.")
    if ENV_TIMEOUT is not None and not isInteger(ENV_TIMEOUT):
        raise ValueError("TIMEOUT must be an integer.")

    run_upload_measurement()
