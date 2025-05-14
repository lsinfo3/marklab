import logging


class ExperimentLogger:
    def __init__(self, logger_name, device_name, modem_name, filename, log_level=logging.INFO):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(log_level)
        self.logger.handlers = []  # Clear existing handlers

        # Create a file handler specifically for this instance
        handler = logging.FileHandler(filename, mode='w')
        formatter = logging.Formatter("%(levelname)s,%(created)f,%(name)s,{},{},%(message)s".format(device_name, modem_name))
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def log_info(self, message):
        print(message)
        self.logger.info(message)

    def log_warning(self, message):
        print(message)
        self.logger.warning(message)

    def log_error(self, message):
        print(message)
        self.logger.error(message)
