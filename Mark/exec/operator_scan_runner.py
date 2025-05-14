import docker
import json
import os

from datetime import datetime, timedelta

from find_modem_port import find_modem_port

import sys
sys.path.append("/home/ubuntu/mark")

from core.utils_api import get_modems, save_operators_in_db

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

SCAN_PERIODS_BY_MODEM = {
    "Quectel_EC21": timedelta(hours=1),
    "Quectel_BG96": timedelta(hours=2)
}

DEFAULT_SCAN_PERIOD = timedelta(hours=1)

def get_current_time():
    return datetime.now().strftime("%Y%m%d%H%M%S")

def log(message):
    current_file = os.path.abspath(__file__)
    log_file_path = f"{os.path.dirname(current_file)}/operator_scan_runner.log"
    with open(log_file_path, "a") as log_file:
        log_file.write(f"{get_current_time()};{message}\n")

def run_operator_scan():
    try:
        modems = get_modems()

        scan_required = False

        for modem in modems:
            name = modem["name"]
            operators = modem["operators"]

            if "timestamp" in operators:
                if name in SCAN_PERIODS_BY_MODEM:
                    scan_period = SCAN_PERIODS_BY_MODEM[name]
                else:
                    scan_period = DEFAULT_SCAN_PERIOD

                last_scan_timestamp = datetime.strptime(operators["timestamp"], TIMESTAMP_FORMAT)
                current_timestamp = datetime.now()
                next_scan_timestamp = last_scan_timestamp + scan_period

                if "manual_scan" in operators and operators["manual_scan"]:
                    modem["scan_required"] = True
                    scan_required = True
                elif current_timestamp >= next_scan_timestamp:
                    # EC21: scan hourly
                    # BG96: scan at most every two hours and only at 3am
                    #       The scan period is still required (if a user manually scans at 2am, don't scan again at 3am)
                    if name == "Quectel_EC21" or current_timestamp.hour == 3:
                        modem["scan_required"] = True
                        scan_required = True

            else:
                modem["scan_required"] = True
                scan_required = True

        if not scan_required:
            return

        log("Starting operator scan.")

        docker_client = docker.from_env()

        for modem in modems:
            if not "scan_required" in modem or not modem["scan_required"]:
                continue

            name = modem["name"]
            log(f"Starting operator scan on {name}.")

            try:
                port = find_modem_port(name)
            except Exception as ex:
                raise Exception(f"Modem port selection failed: {ex}")

            log(f"Found port {port} for modem {name}.")

            try:
                container = docker_client.containers.run(
                    "scan-operator",
                    detach=True,
                    privileged=True,
                    volumes=["/var/run/dbus:/var/run/dbus"],
                    environment=[
                        f"MODEM={name}", f"PORT={port}", f"PC_NAME=Mark"
                    ],
                    stop_signal="SIGINT"
                )
                container.wait()
                logs = container.logs().decode("utf-8")

                container.remove()

                if not "#RESPONSE#" in logs:
                    lines = logs.splitlines()

                    if len(lines) > 0:
                        err = lines[len(lines)-1]

                        if "Error while getting operators: " in err:
                            err = f"AT command response: {err.split("Error while getting operators: ")[1]}"
                    else:
                        err = "No output"

                    raise RuntimeError(f"Error in container: {err}")

                scan_response = json.loads(logs.split("#RESPONSE#")[1].strip())

                if not isinstance(scan_response, dict):
                    raise RuntimeError("Scan response is not a dictionary")

                if not "level" in scan_response:
                    raise RuntimeError("Invalid scan response")

                if scan_response["level"] == "ERROR":
                    raise RuntimeError(scan_response["message"])

                timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
                operators = {"available": True, "timestamp": timestamp, "operators": scan_response["message"]}

                for operator in operators["operators"]:
                    if operator["name"] == "E-Plus":
                        operator["name"] = "o2 - de"

                    if operator["long_name"] == "E-Plus":
                        operator["long_name"] = "o2 - de"

                    if operator["act"] == "0":
                        operator["act_as_text"] = "2G"
                    elif operator["act"] == "2":
                        operator["act_as_text"] = "3G"
                    elif operator["act"] == "7":
                        operator["act_as_text"] = "LTE"
                    elif operator["act"] == "8":
                        operator["act_as_text"] = "LTE-M"
                    elif operator["act"] == "9":
                        operator["act_as_text"] = "NB-IoT"
                    else:
                        operator["act_as_text"] = operator["act"]

                log(f"Found {len(scan_response["message"])} operators on {name}.")
            except Exception as ex1:
                log(f"Error while executing periodic operator scan for modem {name}: {ex1}")
                timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
                operators = {"available": False, "timestamp": timestamp, "message": str(ex1)}

                if "operators" in modem["operators"]:
                    operators["operators"] = modem["operators"]["operators"]
                    log(f"Restored {len(operators["operators"])} previous operators")

            try:
                save_operators_in_db(name, operators)
                log(f"Operator scan result for {name} saved successfully.")
            except Exception as ex1:
                log(f"Error while saving operator scan result for {name}: {ex1}")

        log("Operator scan completed successfully.")
    except Exception as ex:
        log(f"Error while executing periodic operator scan: {ex}")
