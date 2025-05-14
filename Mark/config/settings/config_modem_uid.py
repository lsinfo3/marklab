# This script is used to configure the modem uids in the system.
# 1. Gets all available modems from ModemManager. If no modems are found, the script exits.
# 2. Restarts the udev service and the modemmanager service.
# 3. Gets the modem information from ModemManager like the AT Device and the system device path.
# 4. Gets the modem information from the AT Device via AT Commands.
# 5. Writes the modem information in /lib/udev/rules.d/78-mm-naming.rules.
# 6. Restarts the udev service and the modemmanager service.
# 7. Writes the modem information in the database and creates a .env.device file with the device id.
# 8. If the device id is already in the .env.device file, the script updates the modem information in the database.

import json
import subprocess
import os
import requests

import sys
sys.path.append("/home/ubuntu/mark")

from core.mmcli_cmds import ModemManager
from core.utils_api import API_URL, REQUEST_HEADERS, REQUEST_TIMEOUT


import dotenv

DEVICE_ENV_PATH = "/home/ubuntu/mark/.env.device"
SERVER_ENV_PATH = "/home/ubuntu/mark/.env.server"

dotenv.load_dotenv(dotenv_path=SERVER_ENV_PATH)

REGISTRATION_KEY = os.getenv("REGISTRATION_KEY")

def get_device_path(modem_info):
    device_path = modem_info.get("System").get("device")
    if not device_path.startswith("/sys"):
        # TODO: this fails if the naming rule has already been setup
        # Because of that you cannot run this script twice
        # (for example if there has been an error after the naming rules have already been setup)
        print(f"Unable to get device path. Error: {device_path}")
        return ValueError(f"Unable to get device path. Error: {device_path}")
    device_path = device_path.replace("/sys", "")
    return device_path


def get_modem_ports(modem_info):
    ports = modem_info.get("System").get("ports")
    ports = ports.replace("\n", "")
    ports = ports.split(",")
    return ports


def get_at_port(mmcli_ports):
    at_port = None
    for port in mmcli_ports:
        if port.__contains__("at"):
            at_port = port
            break
    at_port = at_port.split("(")[0].strip()
    return at_port


def generate_modem_name(at_port):
    """
    Run ATCommand ATI and get modem name
    :param at_port: Device port of the modem. E.g. /dev/ttyUSB0
    :return: Tuple of modem name
    """
    ati_response = subprocess.run(["sudo", "bash", "/home/ubuntu/mark/core/at_runner.sh", at_port, "ATI"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  universal_newlines=True)
    if ati_response.returncode != 0:
        print(f"Unable to get modem information. Error: {ati_response}")
        raise ValueError(f"Unable to get modem information. Error: {ati_response}")
    ati_response = ati_response.stdout
    if ati_response.__contains__("ERROR"):
        print(f"Unable to get modem information. Message contains ERROR. Error: {ati_response}")
        raise ValueError(f"Unable to get modem information. Error: {ati_response}")
    name1 = ati_response.split("\n")[1]
    name2 = ati_response.split("\n")[2]
    if name1.__contains__(":"):
        name1 = name1.split(":")[1].strip()
    if name2.__contains__(":"):
        name2 = name2.split(":")[1].strip()
    return name1, name2


def set_naming_rules(modems):
    with open("/lib/udev/rules.d/78-mm-naming.rules", "w") as f:
        f.write('ACTION!="add|change|move|bind", GOTO="mm_naming_rules_end"\n')
        for modem in modems:
            f.write(f'DEVPATH=="{modem[2]}",ENV{{ID_MM_PHYSDEV_UID}}="{modem[1]}"\n')
        f.write('LABEL="mm_naming_rules_end"')


def restart_udevadm_systemctl():
    subprocess.run(["sudo", "udevadm", "control", "--reload-rules"])
    subprocess.run(["sudo", "udevadm", "trigger"])
    subprocess.run(["sudo", "systemctl", "restart", "ModemManager"])


def check_device_id_exists():
    # check if device path file exists and if DEVICE_ID exists
    if not os.path.exists(DEVICE_ENV_PATH):
        print(f"Device path file does not exist.")
        return False, None

    dotenv.load_dotenv(dotenv_path=DEVICE_ENV_PATH)
    device_id = os.getenv("DEVICE_ID")
    if device_id is None:
        print(f"DEVICE_ID does not exist in .env.device file.")
        return False, None
    return True, device_id


def get_ip_address():
    ip_address = subprocess.run(["hostname", "-I"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True)
    if ip_address.returncode != 0:
        print(f"Unable to get ip address. Error: {ip_address}")
        raise ValueError(f"Unable to get ip address. Error: {ip_address}")
    ip_address = ip_address.stdout
    ip_address = ip_address.split(" ")[0]
    return ip_address


def set_device_id_and_api_key_to_env(device_id, api_key):
    dotenv.set_key(dotenv_path="/home/ubuntu/mark/.env.device", key_to_set="DEVICE_ID", value_to_set=str(device_id))
    dotenv.set_key(dotenv_path="/home/ubuntu/mark/.env.device", key_to_set="API_KEY", value_to_set=api_key)


def main():
    print("Starting modem configuration.")
    print("1. Get available modems")
    available_modems = ModemManager.available_modems()

    modems = []  # list of items (modem_id, modem_name, device_path, at_port, supports)

    if len(available_modems) == 0:
        print("No modems found.")
        return

    # 2. For each modem get config information like AT Device, system device running on
    print("2./3./4. Get modem info")
    for modem in available_modems:
        # get modem id
        modem_id = modem[0]
        modem_info = ModemManager.get_modem_dict(modem_id)
        modem_info = json.loads(modem_info)

        # get system device running on
        device_path = get_device_path(modem_info)

        usb_ports = get_modem_ports(modem_info)

        # get port with at
        at_port = f'/dev/{get_at_port(usb_ports)}'

        # 3./4. from at device get modem information
        name1, name2 = generate_modem_name(at_port)

        modem_name = f"{name1}_{name2}"

        # Hardcode these for now since the output of the most recent supported mmcli version is either
        # not consistent (Quectel BG96 has "gsm-umts, lte" but the output should be "2G, NB-IoT, LTE-M")
        if modem_name == "Quectel_BG96":
            supports = "2G, LTE-M, NB-IoT"
        elif modem_name == "Quectel_EC21":
            supports = "2G, 3G, LTE"
        else:
            # Fall back to previous behavior for unknown modems
            supports = modem_info.get("Hardware").get("supported")

        modems.append((modem_id, modem_name, device_path, at_port, supports))
        print(f"Modem {modem_id} - {modem_name} - {device_path} - {at_port} - {supports}")

    print("5. Writing to /lib/udev/rules.d/78-mm-naming.rules")
    set_naming_rules(modems)

    print("6. Restarting udev service and modemmanager service")
    restart_udevadm_systemctl()

    print("7. Sending modem information to server and creating a .env file")

    modem_info = [{
        "name": modem[1],
        "port": modem[3],
        "ability": modem[4]
    } for modem in modems]

    device_id_exists = check_device_id_exists()

    if device_id_exists[0]:
        # update modem information in database
        print("Updating modem information in database.")

        response = requests.post(f"{API_URL}/modems/", headers=REQUEST_HEADERS, verify=False, timeout=REQUEST_TIMEOUT, json=modem_info)
        response.raise_for_status()
        return

    ip_address = get_ip_address()

    print("Registering device.")

    response = requests.post(f"{API_URL}/register_device/", headers={'Content-Type': 'application/json', 'X-Registration-Key': REGISTRATION_KEY}, verify=False, timeout=REQUEST_TIMEOUT, json={
        "ip_address": ip_address
    })
    response.raise_for_status()
    response_json = response.json()
    device_id = response_json["device_id"]
    api_key = response_json["api_key"]

    # add device id to .env.device file, if device id is not already in the file
    set_device_id_and_api_key_to_env(device_id, api_key)

    response = requests.post(f"{API_URL}/modems/", headers={'Content-Type': 'application/json', 'X-API-KEY': api_key}, verify=False, timeout=REQUEST_TIMEOUT, json=modem_info)
    response.raise_for_status()

    print("Done.")


if __name__ == "__main__":
    main()
