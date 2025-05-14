from time import sleep
from core.mmcli_cmds import ModemManager
from core.at_cmds import ATCommands
from core.uhub_runner import UhubRunner
from core.logger import Logger
from core.runner import Runner
import os

ENV_MODEM = os.environ.get('MODEM')  # should be Quectel_EC21 or Quectel_BG96
ENV_PORT = os.environ.get('PORT')  # should be the port of the modem
ENV_BAUDRATE = os.environ.get('BAUDRATE', 115200)  # should be the baudrate of the modem
ENV_TIMEOUT = os.environ.get('TIMEOUT', 1)  # should be the timeout of the modem
ENV_WAIT_TIME = os.environ.get('WAIT_TIME', 120)  # should be the wait time for the modem RESPONSE
ENV_DEVICE_NAME = os.environ.get('PC_NAME')  # should be your rasp name
ENV_ACCESS_TECH = os.environ.get('ACCESS_TECH', "all")  # Should be <all, 0, 7, 8, 9> -> 0 = GSM, 8 = lte-m, 9 = nbiot
ENV_BAND = os.environ.get('BAND', "False")  # should be the band value
ENV_GSMBANDVAL = os.environ.get('GSMBANDVAL', "0F")  # should be the gsm band value
ENV_CATM1BANDVAL = os.environ.get('CATM1BANDVAL', "0000000000080000")  # should be the catm1 band value
ENV_CATNB1BANDVAL = os.environ.get('CATNB1BANDVAL', "0000000000080000")  # should be the catnb1 band value

LOGGER = Logger('modem-act-setup', ENV_DEVICE_NAME, ENV_MODEM)

ENV_IOTOPMODE = 2  # should be the iot modem number (0, 1, 2)
ENV_NWSCANSEQ = "030201"  # should be the rat search sequence e.g. 030201 -> 01: GSM, 02: LTE-M, 03: NB-IoT
ENV_SCANMODE = 0  # should be the scan mode (0: automatic, 1: gsm, 3: LTE)


def set_config_access_tech_setting():
    global ENV_IOTOPMODE
    global ENV_NWSCANSEQ
    global ENV_SCANMODE

    if ENV_ACCESS_TECH == "0":
        ENV_NWSCANSEQ = "01"  # set rat search sequence to 01 -> GSM
        ENV_SCANMODE = 1
    elif ENV_ACCESS_TECH == "8":
        ENV_IOTOPMODE = 0  # set iot modem number to 0 -> LTE-M
        ENV_NWSCANSEQ = "02"  # set rat search sequence to 02 -> LTE-M
        ENV_SCANMODE = 3  # set scan mode to 3 -> LTE
    elif ENV_ACCESS_TECH == "9":
        ENV_IOTOPMODE = 1  # set iot modem number to 1 -> NB-IoT
        ENV_NWSCANSEQ = "03"  # set rat search sequence to 03 -> NB-IoT
        ENV_SCANMODE = 3  # set scan mode to 3 -> LTE


def config_rat():
    if ENV_BAND.casefold() == "True".casefold():
        LOGGER.log_info("Configuring band.")
        band_config = ATCommands.set_band_config(ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, ENV_WAIT_TIME, ENV_GSMBANDVAL,
                                                 ENV_CATM1BANDVAL, ENV_CATNB1BANDVAL, logger=LOGGER)
        if not band_config:
            LOGGER.log_error(f"Failed configuring band.")
            return False

    LOGGER.log_info("Configuring RAT sequence.")
    rat_sequence_config = ATCommands.set_rat_search_sequence(ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, ENV_WAIT_TIME,
                                                             ENV_NWSCANSEQ, logger=LOGGER)
    if not rat_sequence_config:
        LOGGER.log_error(f"Failed configuring RAT sequence.")
        return False

    LOGGER.log_info("Configuring RAT mode.")
    rat_mode_config = ATCommands.set_rat_search_mode(ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, ENV_WAIT_TIME,
                                                     ENV_SCANMODE, logger=LOGGER)
    if not rat_mode_config:
        LOGGER.log_error(f"Failed configuring RAT mode.")
        return False

    LOGGER.log_info("Configuring IoT mode.")
    iot_mode_config = ATCommands.set_iotopmode(ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, ENV_WAIT_TIME, ENV_IOTOPMODE,
                                               logger=LOGGER)
    if not iot_mode_config:
        LOGGER.log_error(f"Failed configuring IoT mode.")
        return False

    LOGGER.log_info("Set operator selection to automatic.")
    operator_selection_config = ATCommands.set_operator(ENV_PORT, ENV_BAUDRATE, ENV_TIMEOUT, ENV_WAIT_TIME, 0,
                                                        logger=LOGGER)
    if not operator_selection_config:
        LOGGER.log_error(f"Failed setting operator selection to automatic.")
        return False
    return True


def setup_act_config():
    # modem_status = get_available_modem()
    # if not modem_status:
    #     LOGGER.log_error("No modem found")
    #     return False

    LOGGER.log_info(f"Enabling modem.")
    _enabled_status, _enabled_message = ModemManager.enable_status_modem(ENV_MODEM)

    if not _enabled_status:
        LOGGER.log_error(f"Enabling modem: {_enabled_message}")
        return False

    set_config_access_tech_setting()
    LOGGER.log_info(f"Varibles - ENV_IOTOPMODE: {ENV_IOTOPMODE}, ENV_NWSCANSEQ: {ENV_NWSCANSEQ}, ENV_SCANMODE: {ENV_SCANMODE}")
    config_status = config_rat()
    if not config_status:
        LOGGER.log_error("Failed configuring RAT-Type.")
        return False

    return True


if __name__ == '__main__':
    if ENV_MODEM is None or ENV_PORT is None:
        LOGGER.log_error("MODEM or PORT not set.")
        exit(1)

    LOGGER.log_info("Starting modem ACT setup.")
    setup_runner = Runner(setup_act_config, alternative_methode=UhubRunner.reboot_modem,
                          alternative_method_args=ENV_MODEM,
                          attempts=3, sleep_time=5)

    setup_result = setup_runner.run(logger=LOGGER)

    if setup_result == setup_runner.RESTARTED:
        LOGGER.log_info("Modem restarted. Process will be restarted in 60 seconds.")
        sleep(60)
        process_result = setup_runner.run(logger=LOGGER, restart=False)

    if setup_result == setup_runner.FAILED:
        LOGGER.log_error("Modem ACT setup failed.")
        exit(1)

    LOGGER.log_info("Modem ACT setup successful.")
