import subprocess
import sys
from time import sleep

sys.path.append("/home/ubuntu/mark/core")


def run_uhub():
    modem_modify_process = subprocess.Popen(
        ["uhubctl", "-l", "1-1.2", "-p", "1", "-a", "2", "-d", "15"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True)

    out, err = modem_modify_process.communicate()
    if modem_modify_process.returncode != 0:
        raise ValueError(err)

    modem_modify_process = subprocess.Popen(
        ["uhubctl", "-l", "1-1.2", "-p", "1", "-a", "2", "-d", "15"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True)

    out, err = modem_modify_process.communicate()

    if modem_modify_process.returncode != 0:
        raise ValueError(err)

    sleep(10)


if __name__ == '__main__':
    try:
        run_uhub()
    except Exception as e:
        print(f"Error while running uhubctl: {e}")
        exit(1)
