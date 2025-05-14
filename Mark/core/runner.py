import time


class Runner:
    FAILED = "failed"
    SUCCESSFUL = "successful"
    RESTARTED = "restarted"

    def __init__(self, main_method, method_args=None, alternative_methode=None, alternative_method_args=None,
                 attempts=3, sleep_time=5):
        self.main_method = main_method
        self.method_args = method_args
        self.alternative_methode = alternative_methode
        self.alternative_method_args = alternative_method_args
        self.attempts = attempts
        self.sleep_time = sleep_time

    def run(self, logger, restart=True):
        # Run the main method
        for i in range(self.attempts):
            # If the method does not take any arguments, call it without any
            if self.method_args is None:
                res = self.main_method()
            else:
                res = self.main_method(self.method_args)
            # # If the method returns True, return successful
            if res:
                return self.SUCCESSFUL

            # If the method fails, log a warning and sleep for the specified time
            if i < self.attempts - 1:
                logger.log_warning(
                    "Failed attempt " + str(i + 1) + " of " + str(self.attempts) + ". Retrying in " + str(
                        self.sleep_time) + " seconds.")
                time.sleep(self.sleep_time)
                print("-" * 50)
            else:
                logger.log_error("Failed attempt " + str(i + 1) + " of " + str(self.attempts) + ".")

        if restart and self.alternative_methode is not None:
            logger.log_info("Restarting modem.")
            if self.alternative_method_args is None:
                res = self.alternative_methode()
            else:
                res = self.alternative_methode(self.alternative_method_args)

            print("-" * 50)

            if res:
                return self.RESTARTED

        return self.FAILED

    def run_with_return(self, logger, restart=False):
        for i in range(self.attempts):
            if self.method_args is None:
                res = self.main_method()
            else:
                res = self.main_method(self.method_args)
            # if res is a tuple, the first element is a boolean and the rest is the return value
            if res[0]:
                return res[1:]

            if i < self.attempts - 1:
                logger.log_warning(
                    "Failed attempt " + str(i + 1) + " of " + str(self.attempts) + ". Retrying in " + str(
                        self.sleep_time) + " seconds.")
                time.sleep(self.sleep_time)
            else:
                logger.log_error("Failed attempt " + str(i + 1) + " of " + str(self.attempts) + ".")

        if restart and self.alternative_methode is not None:
            logger.log_info("Restarting modem.")
            if self.alternative_method_args is None:
                res = self.alternative_methode()
            else:
                res = self.alternative_methode(self.alternative_method_args)
            if res:
                return self.RESTARTED

        return self.FAILED
