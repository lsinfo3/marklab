from core.at_runner import ATRunner
import json
import time
import traceback


class ATCommands:
    @classmethod
    def reboot_modem(cls, _port, _baudrate=115200, _timeout=30, _wait_time=120):
        """
        Resets the modem for over a given port.
        :param _port: serial port
        :param _baudrate: baudrate
        :param _timeout: timeout
        :param _wait_time: wait time for RESPONSE
        :return: Returns status of the process: true or false.
        """
        try:
            with ATRunner(_port, _baudrate, _timeout, _wait_time) as at_runner:
                at_result = at_runner.send(f"AT+CFUN=1,1")
                at_result = at_runner.format_response(at_result)
                return at_result.__contains__("OK")
        except OSError as e:
            # An Input/output error might occur because we cannot read from the port as it is going down
            print(f"Reading reboot response failed, modem is probably rebooting anyway: {str(e)}")
            print(f"Continuing in 10 seconds")
            time.sleep(10)
            return True
        except Exception as e:
            print(traceback.format_exc())
            return False

    @classmethod
    def process_cfun(cls, _port, _baudrate, _timeout, _wait_time, _mode=1, logger=None):
        """
        :param logger: Logger to log errors
        :param _mode: 0=Minimum functionality, 1=Full functionality, 4=Disable both transmitting and receiving RF signals
        :param _port: serial port
        :param _baudrate: baudrate
        :param _timeout: timeout
        :param _wait_time: wait time for RESPONSE
        """
        try:
            with ATRunner(_port, _baudrate, _timeout, _wait_time) as at_runner:
                at_result = at_runner.send(f"AT+CFUN={_mode}")
                at_result = at_runner.format_response(at_result)
                if at_result.__contains__("OK"):
                    return True
        except Exception as e:
            at_result = str(e)

        if logger is not None:
            logger.log_error(f"Error while setting modem functionality: {at_result}. Mode: {_mode}")

        return False

    @classmethod
    def set_minimum_functionality_modem(cls, _port, _baudrate, _timeout, _wait_time, logger=None):
        """
        :param logger: Logger to log errors
        :param _port: serial port
        :param _baudrate: baudrate
        :param _timeout: timeout
        :param _wait_time: wait time for RESPONSE
        :return: Returns status of the process: true or false.
        """
        try:
            with ATRunner(_port, _baudrate, _timeout, _wait_time) as at_runner:
                at_result = at_runner.send("AT+CFUN=0")
                at_result = at_runner.format_response(at_result)
                if at_result.__contains__("OK"):
                    return True
        except Exception as e:
            at_result = str(e)

        if logger is not None:
            logger.log_error(f"Error while setting minimum functionality: {at_result}")

        return False

    @classmethod
    def set_full_functionality_modem(cls, _port, _baudrate, _timeout, _wait_time, logger=None):
        """
        :param _port: serial port
        :param _baudrate: baudrate
        :param _timeout: timeout
        :param _wait_time: wait time for RESPONSE
        :param logger: Logger to log errors
        :return:
        """
        try:
            with ATRunner(_port, _baudrate, _timeout, _wait_time) as at_runner:
                at_result = at_runner.send("AT+CFUN=1")
                return at_result.__contains__("OK")
        except Exception as e:
            at_result = str(e)

        if logger is not None:
            logger.log_error(f"Error while setting full functionality: {at_result}")

        return False

    @classmethod
    def disable_modem(cls, _port, _baudrate, _timeout, _wait_time, logger=None):
        """
        :param _port: serial port
        :param _baudrate: baudrate
        :param _timeout: timeout
        :param _wait_time: wait time for RESPONSE
        :param logger: Logger to log errors
        :return:
        """
        try:
            with ATRunner(_port, _baudrate, _timeout, _wait_time) as at_runner:
                at_result = at_runner.send("AT+CFUN=4")
                at_result = at_runner.format_response(at_result)
                if at_result.__contains__("OK"):
                    return True
        except Exception as e:
            at_result = str(e)

        if logger is not None:
            logger.log_error(f"Error while disabling modem: {at_result}")

        return False

    @classmethod
    def set_iotopmode(cls, _port, _baudrate, _timeout, _wait_time, _mode=2, _effect=1, logger=None):
        """
        Set IoT operation mode. Possible values: 0=LTE-M, 1=NB-IoT, 2=LTE-M+NB-IoT. Default: 2
        :param logger: Logger to log errors
        :param _port: serial port
        :param _baudrate: baudrate
        :param _timeout: timeout
        :param _wait_time: wait time for RESPONSE
        :param _mode: 0=LTE-M, 1=NB-IoT, 2=LTE-M+NB-IoT
        :param _effect: 0=Take effect after UE reboots, 1=Take effect immediately
        :return:
        """
        try:
            with ATRunner(_port, _baudrate, _timeout, _wait_time) as at_runner:
                at_result = at_runner.send(f"AT+QCFG=\"iotopmode\",{_mode},{_effect}")
                at_result = at_runner.format_response(at_result)
                if at_result.__contains__("OK"):
                    return True
        except Exception as e:
            at_result = str(e)

        if logger is not None:
            logger.log_error(f"Error while setting IoT operation mode: {at_result}")

        return False

    @classmethod
    def set_rat_search_sequence(cls, _port, _baudrate, _timeout, _wait_time, _sequence="030201", _effect=1, logger=None):
        """
        Set RAT search sequence. Possible values: 0=GSM, 2=LTE-M, 3=NB-IoT. Default: 030201.
        :param logger: Logger to log errors
        :param _effect: 0=Take effect after UE reboots, 1=Take effect immediately
        :param _port: serial port
        :param _baudrate: baudrate
        :param _timeout: timeout
        :param _wait_time: wait time for RESPONSE
        :param _sequence: sequence of RATs. 0=GSM, 2=LTE-M, 3=NB-IoT
        :return: RESPONSE
        """
        try:
            with ATRunner(_port, _baudrate, _timeout, _wait_time) as at_runner:
                at_result = at_runner.send(f"AT+QCFG=\"nwscanseq\",{_sequence},{_effect}")
                at_result = at_runner.format_response(at_result)
                if at_result.__contains__("OK"):
                    return True
        except Exception as e:
            at_result = str(e)

        if logger is not None:
            logger.log_error(f"Error while setting RAT search sequence: {at_result}")

        return False

    @classmethod
    def set_rat_search_mode(cls, _port, _baudrate, _timeout, _wait_time, _mode=3, _effect=1, logger=None):
        """
        Set RAT search mode. Possible values: 0=Automatic, 1=GSM only, 3=LTE only. Default: 3
        :param logger: Logger to log errors
        :param _effect: 0=Take effect after UE reboots, 1=Take effect immediately
        :param _port: serial port
        :param _baudrate: baudrate
        :param _timeout: timeout
        :param _wait_time: wait time for RESPONSE
        :param _mode: 0=Automatic, 1=Manual
        :return: RESPONSE of AT command
        """
        try:
            with ATRunner(_port, _baudrate, _timeout, _wait_time) as at_runner:
                at_result = at_runner.send(f"AT+QCFG=\"nwscanmode\",{_mode},{_effect}")
                at_result = at_runner.format_response(at_result)
                if at_result.__contains__("OK"):
                    return True
        except Exception as e:
            at_result = str(e)

        if logger is not None:
            logger.log_error(f"Error while setting RAT search mode: {at_result}")

        return False

    @classmethod
    def set_band_config(cls, _port, _baudrate, _timeout, _wait_time, _gsmbandval="0F", _catm1bandval="0000000000080000",
                        _catnb1bandval="0000000000080000", _effect=1, logger=None):
        """
        Set band configuration.
        :param logger: Logger to log errors
        :param _port: serial port
        :param _baudrate: baudrate
        :param _timeout: timeout
        :param _wait_time: wait time for RESPONSE
        :param _gsmbandval: A hexadecimal value that specifies the GSM frequency band.
        :param _catm1bandval: A hexadecimal value that specifies the LTE Cat M1 frequency band.
        :param _catnb1bandval: A hexadecimal value that specifies the LTE Cat NB1 frequency band.
        :param _effect: 0=Take effect after UE reboots, 1=Take effect immediately
        :return: RESPONSE of AT command
        """
        try:
            with ATRunner(_port, _baudrate, _timeout, _wait_time) as at_runner:
                at_result = at_runner.send(f"AT+QCFG=\"band\",{_gsmbandval},{_catm1bandval},{_catnb1bandval},{_effect}")
                at_result = at_runner.format_response(at_result)
                if at_result.__contains__("OK"):
                    return True
        except Exception as e:
            at_result = str(e)

        if logger is not None:
            logger.log_error(f"Error while setting band config: {at_result}")

        return False

    @classmethod
    def reformat_operator_info(cls, operator):
        data = operator.split(",")

        if len(data) < 5:
            return None

        data = [x.replace('"', "") for x in data]
        return {"status": data[0], "long_name": data[1], "name": data[2], "numeric_name": data[3], "act": data[4]}

    @classmethod
    def get_operators(cls, _port, _baudrate, _timeout, _wait_time):
        """
        Get available operators.
        :param _port: serial port
        :param _baudrate: baudrate
        :param _timeout: timeout
        :param _wait_time: wait time for RESPONSE
        :return: RESPONSE of AT command
        """
        try:
            with ATRunner(_port, _baudrate, _timeout, _wait_time) as at_runner:
                at_result = at_runner.send("AT+COPS=?")
                at_result = at_runner.format_response(at_result)

                if at_result.__contains__("OK"):
                    at_result = at_result.replace("OK", "").replace("+COPS: ", "")
                    if at_result.__contains__(",,"):
                        at_result = at_result.split(",,")[0]

                    at_result = at_result.split("),(")
                    at_result = [x.replace("(", "") for x in at_result]
                    at_result = [x.replace(")", "") for x in at_result]
                    at_result = [x for x in at_result if x[0] != "3"]

                    parsed_operators = []

                    for operator in at_result:
                        operator_dict = cls.reformat_operator_info(operator)

                        if operator_dict is None:
                            continue

                        parsed_operators.append(operator_dict)

                    return json.dumps(parsed_operators)

                return at_result
        except Exception as e:
            return f"ERROR: {str(e)}"

    @classmethod
    def get_current_operator(cls, _port, _baudrate, _timeout, _wait_time):
        """
        Get current operator.
        :param _port: serial port
        :param _baudrate: baudrate
        :param _timeout: timeout
        :param _wait_time: wait time for RESPONSE
        :return: RESPONSE of AT command
        """
        try:
            with ATRunner(_port, _baudrate, _timeout, _wait_time) as at_runner:
                at_result = at_runner.send("AT+COPS?")

                if at_result.__contains__("OK"):
                    at_result = at_result.replace("\r\n", "")
                    at_result = at_result.replace("\n", "")
                    at_result = at_result.replace("\r", "")
                    at_result = at_result.replace("OK", "")
                    at_result = at_result.replace("+COPS: ", "")
                    at_result = at_result.strip()
                    if at_result.__contains__("AT+COPS?"):
                        at_result = at_result.replace("AT+COPS?", "")
                    if not at_result.__contains__(","):
                        at_result = None

                return at_result
        except Exception as e:
            return f"ERROR: {str(e)}"

    @classmethod
    def set_operator(cls, _port, _baudrate, _timeout, _wait_time, _operator, logger=None):
        """
        Set operator.
        :param logger: Logger to log errors
        :param _operator: operator
        :param _port: serial port
        :param _baudrate: baudrate
        :param _timeout: timeout
        :param _wait_time: wait time for RESPONSE
        :return: RESPONSE of AT command
        """
        try:
            with ATRunner(_port, _baudrate, _timeout, _wait_time) as at_runner:
                at_result = at_runner.send(f"AT+COPS={_operator}")
                if at_result.__contains__("OK"):
                    return True
        except Exception as e:
            at_result = str(e)

        if logger is not None:
            logger.log_error(f"Error while setting operator: {at_result}")

        return False

    @classmethod
    def get_imsi(cls, _port, _baudrate, _timeout, _wait_time, logger=None):
        """
        Get IMSI.
        :param _port: serial port
        :param _baudrate: baudrate
        :param _timeout: timeout
        :param _wait_time: wait time for RESPONSE
        :param logger: Logger to log errors
        :return: RESPONSE of AT command
        """
        try:
            with ATRunner(_port, _baudrate, _timeout, _wait_time) as at_runner:
                at_result = at_runner.send("AT+CIMI")
                if at_result.__contains__("OK"):
                    at_result = at_result.removeprefix("AT+CIMI")
                    at_result = at_runner.format_response(at_result)
                    return at_result
        except Exception as e:
            logger.log_error(f"Exception while getting IMSI: {str(e)}")
            return None

        if logger is not None:
            logger.log_error(f"Error while getting IMSI: {at_result}")

        return None

    @classmethod
    def run_command(cls, _port, _command, _baudrate=115200, _timeout=30, _wait_time=120):
        """
        Run command.
        :param _command: command to be run
        :param _port: serial port
        :param _baudrate: baudrate
        :param _timeout: timeout
        :param _wait_time: wait time for RESPONSE
        :return: status and response of AT command
        """
        try:
            with ATRunner(_port, _baudrate, _timeout, _wait_time) as at_runner:
                at_result = at_runner.send(_command)
                if at_result.__contains__("OK"):
                    return True, at_result
        except Exception as e:
            at_result = str(e)

        return False, at_result
