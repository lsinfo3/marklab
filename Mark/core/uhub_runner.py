import pyudev
import subprocess
import re
from time import sleep

class UhubRunner:
    @classmethod
    def get_relevant_ids(cls, device_path):
        """
        Gets the vendor and model id of the device.
        :return:
        """
        try:
            context = pyudev.Context()
            device = pyudev.Devices.from_device_file(context, device_path)

            id_model_id = device.get('ID_MODEL_ID', '')
            id_vendor_id = device.get('ID_VENDOR_ID', '')

            if id_model_id == '' or id_vendor_id == '':
                return None, None

            return id_vendor_id, id_model_id
        except Exception as e:
            print(f"Error while getting relevant ids: {e}")
            return None, None

    @classmethod
    def get_relevant_port(cls, relevant_MODEL_VENDOR_ID="2c7c:0296"):
        """
        Gets the relevant ports. The relevant ports are the ports that are not the Master Brick or from the hub 2.
        :return: The relevant ports.
        """
        port = None
        try:
            devices = subprocess.Popen(["uhubctl", "-l", "1-1.2"], stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       universal_newlines=True)
            out, err = devices.communicate()
            lines = out.split("\n")
            for line in lines:
                if line.__contains__(relevant_MODEL_VENDOR_ID):
                    port = re.search(r"Port (\d+):", line).group(1)
                    break

            return port

        except Exception as e:
            print(f"Error while getting ports: {e}")
            return None


    @classmethod
    def get_uhub_port(cls, model_id, vendor_id):
        """
        Gets the port of the modem using the uhubctl command.
        :param model_id: ID of the model.
        :param vendor_id: ID of the vendor.
        :return: The port of the modem.
        """
        try:
            # Get port for the modem
            devices = subprocess.Popen(["uhubctl", "-l", "1-1.2"],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       universal_newlines=True)
            out, err = devices.communicate()
            lines = out.split("\n")
            port = None
            for line in lines:
                if vendor_id in line and model_id in line:
                    # Port 1: 0503 power highspeed enable connect [2c7c:0296 Qualcomm, Incorporated Qualcomm CDMA Technologies MSM 8bfbe455]
                    port = re.search(r"Port (\d+):", line).group(1)
                    break
            if port is None:
                Exception("Error: Could not find port for the modem")
            return port
        except Exception as e:
            raise Exception(f"Error while getting port: {e}")

    @classmethod
    def print_status_devices(cls):
        """
        Prints the status of the devices using the uhubctl command.
        """

        try:
            devices = subprocess.Popen(["uhubctl", "-l", "1-1.2"],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       universal_newlines=True)
            out, err = devices.communicate()
            print("-" * 50)
            print("-" * 50)
            print(out)
            print("-" * 50)
            print("-" * 50)
        except Exception as e:
            print(f"Error while getting status of devices: {e}")

    @classmethod
    def reboot_modem(cls, modem_name):
        """
        Reboots the modem using the uhubctl command. The uhubctl command is used to control USB power per port.
        :return: True if the modem was rebooted successfully, False otherwise.
        """

        try:

            relevant_MODEL_VENDOR_ID = "2c7c:0296"
            if modem_name == "Quectel_EC21":
                relevant_MODEL_VENDOR_ID = "2c7c:0121"

            port = cls.get_relevant_port(relevant_MODEL_VENDOR_ID)
            if port is None:
                print("Error: Could not find port for the given modem. Set the port manually.")

                if modem_name == "Quectel_EC21":
                    port = "1"
                else:
                    port = "2"

            modem_modify_process = subprocess.Popen(
                ["uhubctl", "-l", "1-1.2", "-p", port, "-a", "2", "-d", "15"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True)

            out, err = modem_modify_process.communicate()

            if err:
                print(f"Error: {err}")
                return False

            sleep(10)
            # print information about the process
            print("\n")

            cls.print_status_devices()

            return True
        except Exception as e:
            print(f"Error: {e}")
            return False


if __name__ == "__main__":
    uhub = UhubRunner()
    print(uhub.reboot_modem("Quectel_EC21"))
