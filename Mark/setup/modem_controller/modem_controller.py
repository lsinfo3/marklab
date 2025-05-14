from core.at_cmds import ATCommands
from core.logger import Logger
import os
from time import sleep
from core.uhub_runner import UhubRunner
from core.runner import Runner
from core.cmd_runner import CommandRunner

ENV_MODEM = os.environ.get('MODEM')  # should be Qualcomm or Quectel
ENV_PORT = os.environ.get('PORT')  # should be the port of the modem
ENV_MODE = os.environ.get('MODE',
                          1)  # should be the modem number (0 = minimum functionality, 1 = full functionality, 4 = Disable both transmitting and receiving RF signals)
ENV_BAUDRATE = os.environ.get('BAUDRATE', 115200)  # should be the baudrate of the modem
ENV_TIMEOUT = os.environ.get('TIMEOUT', 30)  # should be the timeout of the modem
ENV_WAIT_TIME = os.environ.get('WAIT_TIME', 120)  # should be the wait time for the modem RESPONSE
ENV_DEVICE_NAME = os.environ.get('PC_NAME', "Mark1")  # should be your rasp name

# init LOGGER
LOGGER = Logger('modem-controller', ENV_DEVICE_NAME, ENV_MODEM)

ARGS = {
    "mode": ENV_MODE,
    "port": ENV_PORT,
    "baudrate": ENV_BAUDRATE,
    "timeout": ENV_TIMEOUT,
    "wait_time": ENV_WAIT_TIME,
}


def set_modem_functionality():
    LOGGER.log_info(f"Setting modem functionality to {ENV_MODE} over {ENV_PORT} (timeout {ENV_TIMEOUT}, wait time {ENV_WAIT_TIME}).")
    if ENV_MODE == "1,1":
        reboot_successful = ATCommands.reboot_modem(ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, ENV_WAIT_TIME)

        if not reboot_successful:
            LOGGER.log_error("Rebooting modem failed")
            return False

        LOGGER.log_info("Modem reboot started, waiting 10 seconds")
        sleep(10)

        count = 15
        interval = 6

        while count > 0:
            LOGGER.log_info(f"Checking if modem is registered in mmcli ({count} attempts remaining)")
            output = CommandRunner.run(f"mmcli -m {ENV_MODEM}")

            if "error:" in output:
                LOGGER.log_info(output.strip())
            else:
                break

            sleep(interval)
            count -= 1

        if count == 0:
            LOGGER.log_error(f"Modem not initialized correctly")
            return False

        return True
    else:
        return ATCommands.process_cfun(ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, ENV_WAIT_TIME, ENV_MODE, LOGGER)


def isInteger(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def isFloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


if __name__ == '__main__':

    # check env variables
    if ENV_TIMEOUT is None or not isInteger(ENV_TIMEOUT):
        LOGGER.log_error(f"Invalid timeout: {ENV_TIMEOUT}")
        exit(1)

    if ENV_WAIT_TIME is None or not isInteger(ENV_WAIT_TIME):
        LOGGER.log_error(f"Invalid wait time: {ENV_WAIT_TIME}")
        exit(1)

    if ENV_MODEM is None:
        LOGGER.log_error("MODEM is not set.")
        exit(1)

    if ENV_PORT is None:
        LOGGER.log_error("PORT is not set.")
        exit(1)

    ENV_TIMEOUT = int(ENV_TIMEOUT)
    ENV_WAIT_TIME = int(ENV_WAIT_TIME)

    # runner for setting modem functionality
    controller_runnner = Runner(set_modem_functionality, alternative_methode=UhubRunner.reboot_modem,
                                alternative_method_args=ENV_MODEM,
                                attempts=3, sleep_time=5)

    controller_status = controller_runnner.run(logger=LOGGER)

    if controller_status == controller_runnner.RESTARTED:
        LOGGER.log_info(f"Modem functionality restarted. Mode {ENV_MODE}.")
        sleep(60)
        controller_status = controller_runnner.run(logger=LOGGER, restart=False)

    if controller_status == controller_runnner.FAILED:
        LOGGER.log_error(f"Modem functionality not set. Mode {ENV_MODE}.")
        exit(1)

    LOGGER.log_info(f"Modem functionality set. Mode {ENV_MODE}.")
