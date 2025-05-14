import json
import os
from time import sleep
import random
from operator_modem_core import OperatorModemCore
from core.at_cmds import ATCommands
from core.uhub_runner import UhubRunner
from core.json_logger import JsonLogger
from core.logger import Logger
from core.mmcli_cmds import ModemManager
from core.network_cmds import NetworkManager
from core.runner import Runner

ENV_MODEM = os.environ.get('MODEM')  # should be Qualcomm or Quectel
ENV_APN = os.environ.get('APN', "em")  # should be em or internet
ENV_CHECK_IMSI = os.environ.get('CHECK_IMSI', "false")  # should be true or false
ENV_IP_TYPE = os.environ.get('IP_TYPE', "ipv4")  # should be ipv4 or ipv6
ENV_DEVICE_NAME = os.environ.get('PC_NAME')  # should be your rasp name
ENV_IP_TARGET = os.environ.get('IP_TARGET', "8.8.8.8")  # should be the destination ip address to ping or check
ENV_CONNECT_OPERATOR = os.environ.get('CONNECT_OPERATOR',
                                      "any")  # should be ANY, RANDOM or operator with format "1,2,"20262",2"
ENV_PORT = os.environ.get('PORT')  # should be the port of the modem
ENV_ACT = os.environ.get('ACCESS_TECH',
                         "all")  # should be the access technology of the modem. Default is all. Options are: 0 = 2G, 2 = 3G, 7 = 4G, 8 = LTE-M, 9 = NB-IoT

# init LOGGER
LOGGER = Logger('operator-modem-setup-detail', ENV_DEVICE_NAME, ENV_MODEM)
JSON_LOGGER = JsonLogger('operator-modem-setup', ENV_DEVICE_NAME, ENV_MODEM)
RESPONSE = {}
args = {
    "pc_name": ENV_DEVICE_NAME,
    "apn": ENV_APN,
    "ip_type": ENV_IP_TYPE,
    "ip_target": ENV_IP_TARGET,
    "connect_operator": ENV_CONNECT_OPERATOR,
    "port": ENV_PORT,
    "access_tech": ENV_ACT,
    "modem": ENV_MODEM
}


def pause(time=3):
    sleep(time)


def get_allowed_operators():
    """
    Get allowed operators based on the IMSI of the SIM card.
    :return: List of allowed operators.
    """
    imsi = ATCommands.get_imsi(ENV_PORT, 115200, 30, 120)
    if imsi is None:
        LOGGER.log_error("IMSI not found")
        return None

    LOGGER.log_info(f"IMSI: {imsi}")
    RESPONSE.update({"imsi": imsi})

    if imsi.startswith("90143"):
        return ["26201"]  # Telekom
    else:
        return ["26202", "26203"]  # Vodafone, O2


def check_any_set_operator():
    """
    Check if the modem is already connected to an operator.
    :return: True if the modem is already connected to an operator, False otherwise.
    """
    LOGGER.log_info("Getting current operator to check if modem is already connected.")
    operator = ATCommands.get_current_operator(ENV_PORT, 115200, 30, 120)

    if operator is not None and operator.__contains__(
            "ERROR"):  # If the message contains ERROR, AT+COPS? failed.
        LOGGER.log_warning(f"Error while getting current operator: {operator}")
        LOGGER.log_warning("Modem is not connected to an operator. Operator will be set to RANDOM.")
        return False

    if operator is not None:  # If the modem is already connected to an operator, the operator will not be changed.
        LOGGER.log_info(f"Current operator: {operator}")
        RESPONSE.update({"operator_inst": operator})
        return True

    return False


def set_random_operator():
    """
    Get available operators and select a random operator.
    :return: True if operator is set successfully, False otherwise. Additionally, the selected operator is returned.
    """
    LOGGER.log_info("Getting available operators to select a random operator.")
    available_operators = ATCommands.get_operators(ENV_PORT, 115200, 30, 120)
    LOGGER.log_info(f"Available operators without filters: {available_operators}")
    # check if available_operators is empty or contains an error
    if not available_operators or available_operators.__contains__("ERROR"):
        LOGGER.log_error(f"Error while getting operators: {available_operators}")
        return False, None

    # check if available_operators is empty
    if available_operators is None or len(available_operators) == 0:
        LOGGER.log_error("No operators found")
        return False, None

    available_operators = json.loads(available_operators)
    # filter operators by access technology if ENV_ACT is set
    if ENV_ACT is not None and ENV_ACT != "all":
        available_operators = [op for op in available_operators if op['act'] == ENV_ACT]

    # filter operators by allowed operators if ENV_APN is set to em
    # if imsi starts with 90143 then Telekom, else Vodafone and O2
    allowed_operators = get_allowed_operators()
    if ENV_APN == "em" and ENV_CHECK_IMSI == "true":
        # get allowed operators

        if allowed_operators is None:
            LOGGER.log_error("No allowed operators found")
            return False, None

        # filter allowed operators
        available_operators = [op for op in available_operators if op['numeric_name'] in allowed_operators]

        # check if available_operators is empty
        if len(available_operators) == 0:
            LOGGER.log_error("No suitable operators found. Allowed operators: " + str(allowed_operators))
            return False, None

    LOGGER.log_info(f"Available operators: {available_operators}")

    # select random operator
    random_operator = random.choice(available_operators)
    operator = f"4,2,{random_operator['numeric_name']},{random_operator['act']}"
    LOGGER.log_info(f"Selected operator: {operator}")
    return True, operator


def check_set_operator(operator, new_operator):
    """
    Check if the operator is set correctly.
    :param operator: Target operator.
    :param new_operator: New operator (only needed if a specific operator should be set).
    :return: True if the operator is set correctly, False otherwise.
    """
    if new_operator is not None and new_operator.__contains__("ERROR"):
        LOGGER.log_error(f"Error while getting current operator: {new_operator}")
        return False

    # check if operator is set correctly
    LOGGER.log_info(f"Check if a operator is set.")
    # answer should be: 0,0,"26202",9
    if new_operator is None or len(new_operator) == 0:
        LOGGER.log_error(f"Fetched operator is empty: {new_operator}")
        return False

    # compare new operator with set operator and check if it is set correctly
    # only compare if mode is not set to 4 (manual/automatic)
    # remove quotes
    if not operator.startswith('4'):
        new_operator = new_operator.replace('"', '')
        LOGGER.log_info(f"Checking operator: {new_operator} == {operator}")
        new_operator = new_operator.replace('"', '')
        operator = operator.replace('"', '')
        #
        # # check if operator is set correctly
        op, act = new_operator.split(",")[2:4]
        oop, oact = operator.split(",")[2:4]
        if op != oop or act != oact:
            LOGGER.log_error(f"Operator not set correctly: {new_operator} != {operator}")
            return False

    return True


def set_operator():
    """
    Set the operator based on the ENV_CONNECT_OPERATOR.
    :return: True if the operator is set successfully, False otherwise.
    """
    operator = ENV_CONNECT_OPERATOR
    if operator.casefold() == "any".casefold():  # If operator is set to ANY, the modem will connect to the first available operator, if it is not already connected.
        if check_any_set_operator():
            return True
        LOGGER.log_info("No initial operator set. Setting operator to RANDOM.")
        operator = "random"  # If the modem is not connected to an operator, the operator will be set to RANDOM.

    if operator.casefold() == "random".casefold():  # If operator is set to RANDOM, the modem will connect to a random operator.
        ro_status, ro_operator = set_random_operator()
        if not ro_status:
            LOGGER.log_error("Setting random operator failed")
            return False
        operator = ro_operator

    LOGGER.log_info(f"Setting operator: {operator}")
    # If operator is set to a specific operator, the modem will connect to the specified operator.
    set_status = ATCommands.set_operator(ENV_PORT, 115200, 30, 120,
                                         operator, logger=LOGGER)

    if not set_status:
        LOGGER.log_error(f"Failed to set operator: {operator}")
        return False

    # get current operator
    new_operator = ATCommands.get_current_operator(ENV_PORT, 115200, 30, 120)

    if new_operator is None:
        LOGGER.log_error(f"Error while getting current operator: {new_operator}")
        return False

    # check if operator is set correctly
    if not check_set_operator(operator, new_operator):
        return False

    # Parse the operator and act from the new response
    oop, oact = new_operator.split(",")[2:4]
    LOGGER.log_info(f"Operator set successfully: {oop}, {oact}")
    RESPONSE.update({"operator_inst": new_operator, "operator": oop, "act": oact})
    return True


def init_modem(modem_id):
    try:
        LOGGER.log_info("Disconnecting existing bearer.")
        _disconnect_status, _disconnect_message = ModemManager.disconnect(modem_id)

        pause()
        # set operator on the basis of ENV_CONNECT_OPERATOR

        LOGGER.log_info("Setting operator. Operator: " + ENV_CONNECT_OPERATOR)
        _set_operator_status = set_operator()
        if not _set_operator_status:
            LOGGER.log_error("Setting operator failed")
            return False

        pause()

        LOGGER.log_info("Activate data connection.")
        # connect modem (mmcli -m <modem> --simple-connect="apn=<apn>;user=<user>;password=<password>")
        _connected_status, _connected_message = ModemManager.connect(modem_id, ENV_APN, ENV_IP_TYPE)
        if not _connected_status:
            LOGGER.log_error(f"Connecting modem: {_connected_message}")
            return False

        RESPONSE.update({"enabled": True})
        RESPONSE.update({"connected": True})

        return True
    except Exception as e:
        LOGGER.log_error(f"{str(e)} \n")
        return False


def init_network(modem_id):
    try:

        LOGGER.log_info("Getting bearer.")
        # get bearer id to get ip address
        _bearer = ModemManager.get_bearer(modem_id)

        if _bearer is None:
            LOGGER.log_error("No bearer available.")
            return False

        LOGGER.log_info(f"Available bearer: {_bearer}")

        LOGGER.log_info("Get available ip address from bearer.")
        # get ip address from bearer
        try:
            _ip_addr, _interface = ModemManager.get_available_ip_info(modem_id, _bearer)

            if _ip_addr is None or _interface is None:
                LOGGER.log_error("No ip address available.")
                return False
        except Exception as e:
            LOGGER.log_error(f"Error while getting ip address: {str(e)}")
            return False

        LOGGER.log_info(f"IP address: {_ip_addr}, Interface: {_interface}")

        LOGGER.log_info("Flushing ip address.")
        _del_ip_status = NetworkManager.del_ip(_ip_addr, _interface)
        if _del_ip_status != "" and _del_ip_status is not None:
            LOGGER.log_info(f"IP address deleted: {_del_ip_status}")

        pause()

        LOGGER.log_info("Bringing up network interface.")
        # bring up network interface
        _link_up_status = NetworkManager.link_up(_interface)
        if _link_up_status != "" and _link_up_status is not None:
            LOGGER.log_info(f"Network interface up: {_link_up_status}")

        pause()

        LOGGER.log_info("Adding ip address to network interface.")
        # add ip address to network interface
        _add_ip_status = NetworkManager.add_ip(_ip_addr, _interface)
        if _add_ip_status != "" and _add_ip_status is not None:
            LOGGER.log_info(f"IP address added: {_add_ip_status}")

        ips = NetworkManager.get_ip_address(interface=_interface)

        # LOGGER.log_info(f"ip addr for interface {_interface}: {ips}")

        pause()

        LOGGER.log_info("Testing connection with ping.")
        ping_check_success, ping_check_error = NetworkManager.ping_check(_interface, ENV_IP_TARGET)

        if not ping_check_success:
            LOGGER.log_error(f"Ping failed: {ping_check_error}")
            return False

        RESPONSE.update({"bearer": _bearer})
        RESPONSE.update({"ip_addr": _ip_addr})
        RESPONSE.update({"interface": _interface})

        return True
    except Exception as e:
        LOGGER.log_error(f"{str(e)} \n")
        return False


def setup_operator():

    RESPONSE.update({"modem_name": ENV_MODEM})

    LOGGER.log_info(f"Enabling modem {ENV_MODEM}.")
    _enabled_status, _enabled_message = ModemManager.enable_status_modem(ENV_MODEM)

    if not _enabled_status:
        LOGGER.log_error(f"Enabling modem {ENV_MODEM}: {_enabled_message.strip()}")

        if "couldn't enable the modem" in _enabled_message:
            modem_info = ModemManager.get_modem_new_dict(ENV_MODEM)

            if modem_info is not None:
                LOGGER.log_info(f'State: {modem_info["modem"]["generic"]["state"]}, reason: {modem_info["modem"]["generic"]["state-failed-reason"]}')
            else:
                LOGGER.log_warning(f"Error getting modem state")

        return False

    if ENV_MODEM == "Quectel_BG96":
        # set rat
        LOGGER.log_info("Setting RAT.")
        rat = OperatorModemCore(logger=LOGGER)
        rat_status = rat.setup_act_config()
        if not rat_status:
            LOGGER.log_error("RAT setup failed")
            return False
        pause()

    # setup the selected modem: enable, disconnect all bearer, set operator, connect to network
    LOGGER.log_info("Initialize modem.")
    operator = init_modem(ENV_MODEM)
    if not operator:
        LOGGER.log_error("Operator initialization failed")
        return False

    # setup network: get bearer, get ip address, add ip address to network interface, ping check
    LOGGER.log_info("Initialize network.")
    network = init_network(ENV_MODEM)
    if not network:
        LOGGER.log_error("Network initialization failed")
        return False

    # disable modem
    # LOGGER.log_info("Disabling modem.")
    # _disabled_status, _disabled_message = ModemManager.disable_status_modem(RELEVANT_MODEM[0])
    # if not _disabled_status:
    #    LOGGER.log_error(f"Disabling modem: {_disabled_message}")
    #    return False
    return True


if __name__ == '__main__':
    if ENV_MODEM is None or ENV_PORT is None:
        JSON_LOGGER.log_error_json("Missing environment variables", arguments=args)
        exit(1)

    LOGGER.log_info("Start setup operator.")

    process_runner = Runner(setup_operator, alternative_methode=UhubRunner.reboot_modem,
                            alternative_method_args=ENV_MODEM,
                            attempts=3, sleep_time=10)

    process_result = process_runner.run(logger=LOGGER)

    if process_result == process_runner.RESTARTED:
        LOGGER.log_info("Modem restarted successfully. Operator initialization will be restarted in 60 seconds.")
        sleep(60)
        process_result = process_runner.run(logger=LOGGER, restart=False)

    if process_result == process_runner.FAILED:
        JSON_LOGGER.log_error_json("Operator initialization failed", arguments=args)
        exit(1)

    # get modem info (mmcli -m <modem>)
    _modem_info = ModemManager.get_modem_info(ENV_MODEM)
    LOGGER.log_info(f"Modem info: {_modem_info}")

    LOGGER.log_info("Operator initialized successfully.")
    RESPONSE = json.dumps(RESPONSE)
    JSON_LOGGER.log_info_json(RESPONSE, arguments=args)
