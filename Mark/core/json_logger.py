import logging
import json
import sys
import time


class JsonLogger:
    def __init__(self, logger_name, device_name, modem_name, log_level=logging.INFO, filepath=None, filename=None):
        self.json_logger = logging.getLogger(logger_name)
        self.json_logger.setLevel(log_level)
        formatter = JSONFormatter(logger_name, device_name, modem_name)

        # Console handler for logging to stdout
        json_console_handler = logging.StreamHandler(sys.stdout)
        json_console_handler.setFormatter(formatter)
        self.json_logger.addHandler(json_console_handler)

        # File handler for logging to a file, if specified
        if filepath is not None and filename is not None:
            json_file_handler = logging.FileHandler(f"{filepath}/{filename}")
            json_file_handler.setFormatter(formatter)
            self.json_logger.addHandler(json_file_handler)

    def log_info_json(self, message, arguments=None):
        print("#RESPONSE#")
        if arguments is None:
            self.json_logger.info(message)
        else:
            self.json_logger.info(message, arguments)

    def log_warning_json(self, message, arguments=None):
        print("#RESPONSE#")
        if arguments is None:
            self.json_logger.warning(message)
        else:
            self.json_logger.warning(message, arguments)

    def log_error_json(self, message, arguments=None):
        print("#RESPONSE#")
        if arguments is None:
            self.json_logger.error(message)
        else:
            self.json_logger.error(message, arguments)


class JSONFormatter(logging.Formatter):
    def __init__(self, logger_name, device_name, modem_name):
        super(JSONFormatter, self).__init__()
        self.logger_name = logger_name
        self.device_name = device_name
        self.modem_name = modem_name

    def format(self, record):
        record_dict = {
            'timestamp': record.created,
            'level': record.levelname,
            'logger': self.logger_name,
            'device': self.device_name,
            'modem': self.modem_name,
            'message': record.getMessage(),
            'arguments': record.args if record.args else None,
        }
        try:
            record_dict['message'] = json.loads(record_dict['message'])
        except json.JSONDecodeError:
            pass
        return json.dumps(record_dict)
