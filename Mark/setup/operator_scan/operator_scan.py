import json
import os
from time import sleep

from core.mmcli_cmds import ModemManager
from core.at_cmds import ATCommands
from core.json_logger import JsonLogger
from core.logger import Logger
from core.runner import Runner

ENV_MODEM = os.environ.get('MODEM')  # should be Qualcomm or Quectel
ENV_PORT = os.environ.get('PORT')  # should be the port of the modem
ENV_BAUDRATE = os.environ.get('BAUDRATE', 115200)  # should be the baudrate of the modem
ENV_TIMEOUT = os.environ.get('TIMEOUT', 1)  # should be the timeout of the modem
ENV_WAIT_TIME = os.environ.get('WAIT_TIME', 120)  # should be the wait time for the modem RESPONSE
ENV_DEVICE_NAME = os.environ.get('PC_NAME')  # should be your rasp name

# init LOGGER
LOGGER = Logger('operator-scan-detail', ENV_DEVICE_NAME, ENV_MODEM)
JSON_LOGGER = JsonLogger('operator-scan', ENV_DEVICE_NAME, ENV_MODEM)

RELEVANT_MODEM = None
OPERATORS = []

args = {
    "baudrate": ENV_BAUDRATE,
    "timeout": ENV_TIMEOUT,
    "wait_time": ENV_WAIT_TIME,
    "device_name": ENV_DEVICE_NAME,
    "modem": ENV_MODEM
}


def get_available_modem():
    """
    :return: True and tuple of the selected modem (modem_id, modem_name) if a modem was found, False otherwise.
    """
    global RELEVANT_MODEM
    # get available modems
    LOGGER.log_info("Getting available modems.")
    modem = ModemManager.available_modems()

    # get selected modem
    if len(modem) == 0:
        LOGGER.log_error("No modem found")
        return False

    for m in modem:
        if m[1].__contains__(ENV_MODEM):
            RELEVANT_MODEM = m
            break

    if RELEVANT_MODEM is None:
        LOGGER.log_error(f"No {ENV_MODEM} modem found")
        return False

    LOGGER.log_info(f"Selected modem: {RELEVANT_MODEM[1]}")
    return True


def scan_operator():
    global OPERATORS

    try:
        # get modem info (mmcli -m <modem>)
        operators = ATCommands.get_operators(ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, ENV_WAIT_TIME)
        if operators.__contains__("ERROR"):
            LOGGER.log_error(f"Error while getting operators: {operators}")
            return False

        if operators is None or len(operators) == 0:
            LOGGER.log_warning("No operator found")
            OPERATORS = []
            return True

        OPERATORS = operators

        return True
    except Exception as e:
        LOGGER.log_error(f"Error: {str(e)} \n")
        return False


def process_scan():
    global OPERATORS

    if ENV_MODEM == "Quectel_BG96":
        LOGGER.log_info("Configuring band.")
        band_config = ATCommands.set_band_config(
            ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, 10,
            "0F", "0000000000080000", "0000000000080000", logger=LOGGER)

        if not band_config:
            LOGGER.log_error(f"Configuring band failed.")

        LOGGER.log_info("Configuring RAT sequence (2G + LTE-M).")
        rat_sequence_config = ATCommands.set_rat_search_sequence(
            ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, 10, "0201", logger=LOGGER)

        if not rat_sequence_config:
            LOGGER.log_error(f"Configuring RAT sequence failed.")

        LOGGER.log_info("Configuring RAT mode (2G + LTE-M).")
        rat_mode_config = ATCommands.set_rat_search_mode(
            ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, 10, 0, 1, logger=LOGGER)

        if not rat_mode_config:
            LOGGER.log_error(f"Configuring RAT mode failed.")

        LOGGER.log_info("Configuring IoT mode (LTE-M).")
        iot_mode_config = ATCommands.set_iotopmode(
            ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, 120, 0, logger=LOGGER)

        if not iot_mode_config:
            LOGGER.log_error(f"Configuring IoT mode failed.")

        LOGGER.log_info(f"Scanning for operators (2G + LTE-M).")

        if not scan_operator():
            return False

        operators_2g_lte_m = [ operator for operator in json.loads(OPERATORS) ]

        LOGGER.log_info(f"Rebooting modem after 2G + LTE-M scan.")

        reboot_result = ATCommands.reboot_modem(ENV_PORT, ENV_BAUDRATE, 30, ENV_WAIT_TIME)

        if not reboot_result:
            LOGGER.log_error(f"Rebooting modem failed.")
            return False

        LOGGER.log_info(f"Modem rebooted successfully.")

        sleep(60)

        LOGGER.log_info("Configuring band.")
        band_config = ATCommands.set_band_config(
            ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, 10,
            "0F", "0000000000080000", "0000000000080000", logger=LOGGER)

        if not band_config:
            LOGGER.log_error(f"Configuring band failed.")

        LOGGER.log_info("Configuring RAT sequence (NB-IoT).")
        rat_sequence_config = ATCommands.set_rat_search_sequence(
            ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, 10, "03", logger=LOGGER)

        if not rat_sequence_config:
            LOGGER.log_error(f"Configuring RAT sequence failed.")

        LOGGER.log_info("Configuring RAT mode (NB-IoT).")
        rat_mode_config = ATCommands.set_rat_search_mode(
            ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, 10, 3, 1, logger=LOGGER)

        if not rat_mode_config:
            LOGGER.log_error(f"Configuring RAT mode failed.")

        LOGGER.log_info("Configuring IoT mode (NB-IoT).")
        iot_mode_config = ATCommands.set_iotopmode(
            ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, 120, 1, logger=LOGGER)

        if not iot_mode_config:
            LOGGER.log_error(f"Configuring IoT mode failed.")

        LOGGER.log_info(f"Scanning for operators (NB-IoT).")

        if not scan_operator():
            return False

        operators_nb_iot = [ operator for operator in json.loads(OPERATORS) if operator["act"] == "9" ]
        OPERATORS = json.dumps(operators_2g_lte_m + operators_nb_iot)
        return True
    else:
        LOGGER.log_info(f"Scanning for operators.")
        return scan_operator()


if __name__ == '__main__':
    LOGGER.log_info("Starting operator scan.")

    process_runner = Runner(process_scan, alternative_methode=ATCommands.reboot_modem, alternative_method_args=ENV_PORT,
                            attempts=3, sleep_time=5)

    process_result = process_runner.run(logger=LOGGER)

    if process_result == process_runner.RESTARTED:
        LOGGER.log_info("Modem restarted successfully. Process will be restarted in 60 seconds.")
        sleep(60)
        process_result = process_runner.run(logger=LOGGER, restart=False)

    if process_result == process_runner.FAILED:
        JSON_LOGGER.log_error_json("Operator scan failed.", arguments=args)
        exit(1)

    if len(OPERATORS) > 0:
        JSON_LOGGER.log_info_json(OPERATORS, arguments=args)
    else:
        JSON_LOGGER.log_error_json("No operator found.", arguments=args)
        exit(1)
