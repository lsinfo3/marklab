from core.mmcli_cmds import ModemManager
from core.at_cmds import ATCommands
import os


class OperatorModemCore:
    def __init__(self, logger):
        self.LOGGER = logger
        self.ENV_MODEM = os.environ.get('MODEM')  # should be Quectel_EC21 or Quectel_BG96
        self.ENV_PORT = os.environ.get('PORT')  # should be the port of the modem
        self.ENV_BAUDRATE = os.environ.get('BAUDRATE', 115200)  # should be the baudrate of the modem
        self.ENV_TIMEOUT = os.environ.get('TIMEOUT', 1)  # should be the timeout of the modem
        self.ENV_WAIT_TIME = os.environ.get('WAIT_TIME', 120)  # should be the wait time for the modem RESPONSE
        self.ENV_DEVICE_NAME = os.environ.get('PC_NAME')  # should be your rasp name
        # todo: in modem setup mit aufnehmen
        self.ENV_ACCESS_TECH = os.environ.get('ACCESS_TECH', "all")  # Should be <all, 0, 7, 8, 9> -> 0 = GSM, 8 = lte-m, 9 = nbiot
        self.ENV_BAND = os.environ.get('BAND', "False")  # should be the band value
        self.ENV_GSMBANDVAL = os.environ.get('GSMBANDVAL', "0F")  # should be the gsm band value
        self.ENV_CATM1BANDVAL = os.environ.get('CATM1BANDVAL', "0000000000080000")  # should be the catm1 band value
        self.ENV_CATNB1BANDVAL = os.environ.get('CATNB1BANDVAL', "0000000000080000")  # should be the catnb1 band value
        self.ENV_IOTOPMODE = 2  # should be the iot modem number (0, 1, 2)
        self.ENV_NWSCANSEQ = "030201"  # should be the rat search sequence e.g. 030201 -> 01: GSM, 02: LTE-M, 03: NB-IoT
        self.ENV_SCANMODE = 0  # should be the scan mode (0: automatic, 1: gsm, 3: LTE)

    def set_config_access_tech_setting(self):
        if self.ENV_ACCESS_TECH == "0":
            self.ENV_NWSCANSEQ = "01"
            self.ENV_SCANMODE = 1
        elif self.ENV_ACCESS_TECH == "8":
            self.ENV_IOTOPMODE = 0
            self.ENV_NWSCANSEQ = "02"
            self.ENV_SCANMODE = 3
        elif self.ENV_ACCESS_TECH == "9":
            self.ENV_IOTOPMODE = 1
            self.ENV_NWSCANSEQ = "03"
            self.ENV_SCANMODE = 3

    def config_rat(self):
        if self.ENV_BAND.casefold() == "True".casefold():
            self.LOGGER.log_info("Configuring band.")
            band_config = ATCommands.set_band_config(self.ENV_PORT, self.ENV_BAUDRATE, self.ENV_TIMEOUT, self.ENV_WAIT_TIME, self.ENV_GSMBANDVAL,
                                                     self.ENV_CATM1BANDVAL, self.ENV_CATNB1BANDVAL, logger=self.LOGGER)
            if not band_config:
                self.LOGGER.log_error(f"Failed configuring band.")
                return False

        self.LOGGER.log_info("Configuring RAT sequence.")
        rat_sequence_config = ATCommands.set_rat_search_sequence(self.ENV_PORT, self.ENV_BAUDRATE, self.ENV_TIMEOUT, self.ENV_WAIT_TIME,
                                                                 self.ENV_NWSCANSEQ, logger=self.LOGGER)
        if not rat_sequence_config:
            self.LOGGER.log_error(f"Failed configuring RAT sequence.")
            return False

        self.LOGGER.log_info("Configuring RAT mode.")
        rat_mode_config = ATCommands.set_rat_search_mode(self.ENV_PORT, self.ENV_BAUDRATE, self.ENV_TIMEOUT, self.ENV_WAIT_TIME,
                                                         self.ENV_SCANMODE, logger=self.LOGGER)

        if not rat_mode_config:
            self.LOGGER.log_error(f"Failed configuring RAT mode.")
            return False

        self.LOGGER.log_info("Configuring IoT mode.")
        iot_mode_config = ATCommands.set_iotopmode(self.ENV_PORT, self.ENV_BAUDRATE, self.ENV_TIMEOUT, self.ENV_WAIT_TIME, self.ENV_IOTOPMODE,
                                                   logger=self.LOGGER)
        if not iot_mode_config:
            self.LOGGER.log_error(f"Failed configuring IoT mode.")
            return False

        self.LOGGER.log_info("Set operator selection to automatic.")
        operator_selection_config = ATCommands.set_operator(self.ENV_PORT, self.ENV_BAUDRATE, self.ENV_TIMEOUT, self.ENV_WAIT_TIME, 0,
                                                            logger=self.LOGGER)
        if not operator_selection_config:
            self.LOGGER.log_error(f"Failed setting operator selection to automatic.")
            return False
        return True

    def setup_act_config(self):

        self.set_config_access_tech_setting()
        self.LOGGER.log_info(f"Varibles - ENV_IOTOPMODE: {self.ENV_IOTOPMODE}, ENV_NWSCANSEQ: {self.ENV_NWSCANSEQ}, ENV_SCANMODE: {self.ENV_SCANMODE}")

        config_status = self.config_rat()
        if not config_status:
            self.LOGGER.log_error("Failed configuring RAT type.")
            return False

        return True
