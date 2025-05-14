import os
import requests

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from dotenv import load_dotenv

load_dotenv(dotenv_path="/home/ubuntu/mark/.env.server")
load_dotenv(dotenv_path="/home/ubuntu/mark/.env.device")

DEVICE_ID = os.getenv("DEVICE_ID")

SERVER_URL = os.getenv("SERVER_URL")
SERVER_URL = SERVER_URL.removesuffix("/")
API_URL = f"{SERVER_URL}/device_api"

REQUEST_HEADERS = {
    'Content-Type': 'application/json',
    'X-API-KEY': os.getenv('API_KEY')
}

REQUEST_HEADERS_NO_JSON = {
    'X-API-KEY': os.getenv('API_KEY')
}

REQUEST_TIMEOUT = 30


def send_health_check_message_to_server(message, status):
    payload = {
        "message": message,
        "status": status,
        "device_id": DEVICE_ID
    }

    try:
        r = requests.post(f"{API_URL}/health/", json=payload, headers=REQUEST_HEADERS, verify=False, timeout=REQUEST_TIMEOUT)
        if r.status_code != 200:
            raise ValueError(f"Unable to send message. Error: {r.text}")
    except Exception as ex:
        raise ValueError(f"Error while sending message: {ex}")

    return r.text


def get_modems():
    response = requests.get(f"{API_URL}/modems/", headers=REQUEST_HEADERS, verify=False, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()["modems"]


def save_operators_in_db(modem_name, operators):
    response = requests.post(f"{API_URL}/modems/", headers=REQUEST_HEADERS, verify=False, timeout=REQUEST_TIMEOUT, json=[{
        "name": modem_name,
        "operators": operators
    }])
    response.raise_for_status()
