import json

from core.cmd_runner import CommandRunner
from core.mmcli_parser import ModemManagerParser


class ModemManager:

    @classmethod
    def available_modems(cls):
        """
        Returns a list of tuples (modem_id, modem_name)
        :return: A list of Modem information.
        """
        cmd = "mmcli -L"
        output = CommandRunner.run(cmd)
        modems = ModemManagerParser.parse_available_modems(output)

        return modems

    @classmethod
    def get_bearer(cls, modem_id):
        """
        Returns the bearer of a modem.
        :param modem_id: The id of the modem.
        :return: The bearer of the modem.
        """

        cmd = f"mmcli -m {modem_id}"
        output = CommandRunner.run(cmd)
        _bearer = ModemManagerParser.parse_modem_bearer(output)
        return _bearer

    @classmethod
    def get_modem_info(cls, modem_id):
        """
        Returns information about a modem.
        :param modem_id: The id of the modem.
        :return: Modem information as a dictionary.

        """
        cmd = f"mmcli -m {modem_id}"
        output = CommandRunner.run(cmd)
        modem_info = ModemManagerParser.parse_modem_info(output)

        return modem_info

    @classmethod
    def get_modem_dict(cls, modem_id):
        """
        Returns information about a modem.
        :param modem_id: The id of the modem.
        :return: Modem information as a dictionary.

        """
        cmd = f"mmcli -m {modem_id}"
        output = CommandRunner.run(cmd)
        modem_info = ModemManagerParser.parse_mmcli_info(output)

        return modem_info

    @classmethod
    def get_modem_new_dict(cls, modem_id):
        """
        :param modem_id: The id of the modem.
        :return: Dictionary generated from mmcli JSON output.
        """
        cmd = f"mmcli -m {modem_id} --output-json"
        output = CommandRunner.run(cmd)

        if output.startswith("error"):
            return None

        try:
            return json.loads(output)
        except Exception:
            return None

    @classmethod
    def enable_status_modem(cls, modem_id):
        """
        Enables a modem.
        :param modem_id: The id of the modem.
        :return: True if the modem was enabled successfully, False otherwise.
        """
        cmd = f"mmcli -m {modem_id} --enable"
        output = CommandRunner.run(cmd)

        if not output.__contains__("successfully"):
            return False, output

        return True, output

    @classmethod
    def disable_status_modem(cls, modem_id):
        """
        Disables a modem.
        :param modem_id: The id of the modem.
        :return: True if the modem was disabled successfully, False otherwise.
        """
        cmd = f"mmcli -m {modem_id} --disable"
        output = CommandRunner.run(cmd)

        if not output.__contains__("successfully"):
            return False, output

        return True, output

    @classmethod
    def get_available_operator(cls, modem_id, timeout=None):
        """
        Scans for available networks.
        :param modem_id: The id of the modem.
        :param timeout: The timeout of the scan.
        :return: A list of available networks.
        """
        cmd = f"mmcli -m {modem_id} --3gpp-scan"
        if timeout is None:
            cmd += f" --timeout {timeout}"

        try:
            output = CommandRunner.run(cmd)
            available_operator = ModemManagerParser.parse_mmcli_info(output)
            if available_operator is None:
                return []
            available_operator = json.loads(available_operator)
            available_operator = available_operator["3GPP scan"]["networks"].split("\n")
            return available_operator
        except Exception as e:
            print(e)
            return []

    @classmethod
    def register_operator(cls, modem_id, operator, act=None):
        """
        Register network operator with specific access technology.
        :param modem_id: The id of the modem
        :param operator: The available operator (e.g. 26202)
        :param act: The access technology.
        :return: Status of this operation
        """
        cmd = f"mmcli -m {modem_id} --3gpp-register-in-operator={operator}"
        if act is not None:
            cmd += "," + act
        output = CommandRunner.run(cmd)
        return output

    @classmethod
    def connect(cls, modem_id, apn, ip_type):
        """
        Connects to a network.
        :param modem_id: The id of the modem.
        :param apn: The APN of the network.
        :param ip_type: The IP type of the network.
        :return: True if the connection was successful, False otherwise.
        """
        cmd = f"mmcli -m {modem_id} --simple-connect='apn={apn},ip-type={ip_type}'"
        output = CommandRunner.run(cmd)

        if not output.__contains__("successfully"):
            return False, output

        return True, output

    @classmethod
    def disconnect(cls, modem_id):
        """
        Disconnects from a network.
        :param modem_id: The id of the modem.
        :return: True if the disconnection was successful, False otherwise.
        """
        cmd = f"mmcli -m {modem_id} --simple-disconnect"
        output = CommandRunner.run(cmd)

        if not output.__contains__("successfully"):
            return False, output

        return True, output

    @classmethod
    def get_available_ip_info(cls, modem_id, bearer_id):
        cmd = f"mmcli -m {modem_id} --bearer={bearer_id}"
        output = CommandRunner.run(cmd)
        bearer_info = ModemManagerParser.parse_modem_info(output)
        addr = bearer_info["address"]
        interface = bearer_info["interface"]
        return addr, interface
