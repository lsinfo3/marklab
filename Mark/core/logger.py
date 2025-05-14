import logging
import sys
import time


class Logger:
    def __init__(self, logger_name, device_name, modem_name, log_level=logging.INFO, filepath=None, filename=None):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(log_level)

        log_formatter = logging.Formatter(
             "%(levelname)s,%(created)f,%(name)s,{},{},%(message)s".format(device_name, modem_name)
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_formatter)
        self.logger.addHandler(console_handler)

        if filepath and filename:
            file_handler = logging.FileHandler(f"{filepath}/{filename}")
            file_handler.setFormatter(log_formatter)
            self.logger.addHandler(file_handler)

    def log_info(self, message):
        self.logger.info(message)

    def log_warning(self, message):
        self.logger.warning(message)

    def log_error(self, message):
        self.logger.error(message)

    def log_exception(self, message):
        self.logger.exception(message)
