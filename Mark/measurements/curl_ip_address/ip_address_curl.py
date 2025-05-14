import os
from core.cmd_runner import CommandRunner
from core.json_logger import JsonLogger

ENV_DEVICE_NAME = os.environ.get('PC_NAME')  # should be your rasp name
ENV_MODEM = os.environ.get('MODEM')  # should be Qualcomm or Quectel
ENV_INTERFACE = os.environ.get('INTERFACE')  # should be the interface of the modem
ENV_URL = os.environ.get('URL', "ifconfig.me/all.json")  # should be the destination ip address to ping or check

args = {
    "device_name": ENV_DEVICE_NAME,
    "modem": ENV_MODEM,
    "interface": ENV_INTERFACE,
    "url": ENV_URL
}

JSON_LOGGER = JsonLogger('curl_ip_address', ENV_DEVICE_NAME, ENV_MODEM)


def run_curl_ip_address():
    try:
        curl_output = CommandRunner.run(f"curl -s --interface {ENV_INTERFACE} {ENV_URL}")
        JSON_LOGGER.log_info_json(curl_output, arguments=args)
    except Exception as e:
        JSON_LOGGER.log_error_json(str(e), arguments=args)


if __name__ == '__main__':

    if ENV_DEVICE_NAME is None or ENV_INTERFACE is None:
        JSON_LOGGER.log_error_json("Error: DEVICE_NAME and INTERFACE must be set", arguments=args)
        exit(1)

    run_curl_ip_address()
