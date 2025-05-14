from core.at_cmds import ATCommands
from core.json_logger import JsonLogger
import os

ENV_MODEM = os.environ.get('MODEM')
ENV_PORT = os.environ.get('PORT')
ENV_BAUDRATE = os.environ.get('BAUDRATE', 115200)
ENV_TIMEOUT = os.environ.get('TIMEOUT', 30)
ENV_WAIT_TIME = os.environ.get('WAIT_TIME', 120)
ENV_DEVICE_NAME = os.environ.get('PC_NAME')
ENV_REPORT_FORMAT = os.environ.get('REPORT_FORMAT', 2)

args = {
    "device_name": ENV_DEVICE_NAME,
    "modem": ENV_MODEM,
    "port": ENV_PORT,
    "baudrate": ENV_BAUDRATE,
    "timeout": ENV_TIMEOUT,
    "wait_time": ENV_WAIT_TIME
}

# init the logger
logger = JsonLogger('network_report', ENV_DEVICE_NAME, ENV_MODEM)


def set_error_message(problem, reason):
    args.update({"problem": problem})
    args.update({"reason": reason})
    logger.log_error_json(f"{problem}: {reason}", arguments=args)
    exit(1)


def get_network_report():
    try:
        command = "AT+CREG"
        # set network report command
        s_nr, s_reason = ATCommands.run_command(ENV_PORT, f"{command}={ENV_REPORT_FORMAT}", _baudrate=ENV_BAUDRATE, _timeout=ENV_TIMEOUT, _wait_time=ENV_WAIT_TIME)
        if not s_nr:
            set_error_message(f"Error while setting the network report command. Command: {command}={ENV_REPORT_FORMAT}", s_reason)

        # get the network report
        network_report, result = ATCommands.run_command(ENV_PORT, f"{command}?", _baudrate=ENV_BAUDRATE, _timeout=ENV_TIMEOUT, _wait_time=ENV_WAIT_TIME)
        # log the network report

        if not network_report:
            set_error_message(f"Error while getting the network report. Command: {command}?", result)

        # extract all the values
        lines = result.splitlines()

        for line in lines:
            if line.startswith("+CREG:"):
                result = line
                break

        if not result.startswith("+CREG:"):
            set_error_message("Error while extracting the network report. No information provided.", result)

        result = result.replace("\r", "")
        result = result.replace("\n", "")
        result = result.split(": ")[1]
        result = result.split(",")

        if len(result) < 5:
            set_error_message("Error while extracting the network report. Information do not match the expected output.", result)

        response = {
            "n": result[0],
            "stat": result[1],
            "lac": result[2],
            "ci": result[3],
            "act": result[4]
        }

        # if the network report has more than 5 values
        # extract the rest of the values
        if len(result) == 7:
            response.update({
                "cause_type": result[5],
                "reject_cause": result[6]
            })

        logger.log_info_json(f"Network report: {response}", arguments=args)
    except Exception as ex:
        logger.log_error_json(f"Error: {ex}", arguments=args)


if __name__ == "__main__":
    # check env modem and port
    if ENV_MODEM is None or ENV_PORT is None:
        logger.log_error_json("MODEM or PORT not set.", arguments=args)
        exit(1)
    # get the network report
    get_network_report()
    exit(0)
