from datetime import datetime
import os


def get_current_time():
    return datetime.now().strftime("%Y%m%d%H%M%S")


def log(_message, _file_name="watchdog.log"):
    # get current file path
    file = os.path.abspath(__file__)
    with open(f"{os.path.dirname(file)}/log/{_file_name}", "a") as f:
        f.write(f"{get_current_time()};{_message}\n")
