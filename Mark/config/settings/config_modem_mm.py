# Description: This script is used to configure ModemManager to ignore a particular device.
# This is needed, otherwise MM and serial interface will conflict and timeout will occur.
# In the first step, the script gets all available ports from the database.
# In the second step, the script gets the device information from the device path.
# In the third step, the script creates a udev rule for the device.
# In the fourth step, the script restarts the udev service and the modemmanager service.


import pyudev
import subprocess

import sys
sys.path.append("/home/ubuntu/mark")

from core.utils_api import get_modems


def get_ports():
    modems = get_modems()
    return [ modem["port"] for modem in modems ]


def get_device_info(device_path):
    context = pyudev.Context()
    device = pyudev.Devices.from_device_file(context, device_path)

    id_path = device.get('ID_PATH', '')
    id_usb_driver = device.get('ID_USB_DRIVER', '')
    id_model_id = device.get('ID_MODEL_ID', '')
    id_vendor_id = device.get('ID_VENDOR_ID', '')
    id_usb_interface_num = device.get('ID_USB_INTERFACE_NUM', '')

    if id_path == '' or id_usb_driver == '' or id_model_id == '' or id_vendor_id == '' or id_usb_interface_num == '':
        raise ValueError("Device information is not complete.")

    return {
        'ID_PATH': id_path,
        'ID_USB_DRIVER': id_usb_driver,
        'ID_MODEL_ID': id_model_id,
        'ID_VENDOR_ID': id_vendor_id,
        'ID_USB_INTERFACE_NUM': id_usb_interface_num,
    }


def create_udev_rule(port, device_info):
    name = port
    if port.__contains__("/"):
        name = port.split("/")[-1]
    try:
        # Create udev rule
        with open(f"/etc/udev/rules.d/99-ignore-{name}.rules", "w") as f:
            f.write(f'SUBSYSTEM=="tty", ENV{{ID_PATH}}=="{device_info["ID_PATH"]}", '
                    f'ENV{{ID_VENDOR_ID}}=="{device_info["ID_VENDOR_ID"]}", ENV{{ID_MODEL_ID}}=="{device_info["ID_MODEL_ID"]}", '
                    f'ENV{{ID_USB_INTERFACE_NUM}}=="{device_info["ID_USB_INTERFACE_NUM"]}", ENV{{ID_USB_DRIVER}}=="{device_info["ID_USB_DRIVER"]}", '
                    f'ENV{{ID_MM_DEVICE_IGNORE}}="1"')
    except Exception as e:
        raise ValueError(f"Unable to create udev rule. Error: {e}")


def main():
    try:
        ports = get_ports()
        for port in ports:
            device_info = get_device_info(port)
            create_udev_rule(port, device_info)

        subprocess.run(["sudo", "udevadm", "control", "--reload-rules"])
        subprocess.run(["sudo", "udevadm", "trigger"])
        subprocess.run(["sudo", "systemctl", "restart", "ModemManager"])
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
