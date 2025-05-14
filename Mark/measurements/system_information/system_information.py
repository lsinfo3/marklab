import os
import time
import signal
import sys
from core.logger import Logger
from core.utils import isInteger, isFloat
import psutil

ENV_DEVICE_NAME = os.environ.get('PC_NAME', "Mark1")  # should be your rasp name
ENV_MODEM = os.environ.get('MODEM', "Quectel_BG96")  # should be Qualcomm or Quectel
ENV_DURATION = os.environ.get('DURATION')  # should be the number of how long you want to run the measurement
ENV_SLEEP = os.environ.get('SLEEP', 5)
LOGGER = Logger('monitor_system', ENV_DEVICE_NAME, ENV_MODEM)


def signal_handler(sigum, frame):
    sys.exit(0)


def run_system_information_measurement():
    """
    Measures system information like cpu usage, memory usage, disk usage, network usage.
    """

    start_time = time.time()
    while True:
        # cpu usage
        cpu_usage = psutil.cpu_percent(interval=None)

        # memory usage
        memory_usage = psutil.virtual_memory().percent
        memory_used = psutil.virtual_memory().used / 1024 / 1024 / 1024

        swap_memory_usage = psutil.swap_memory().percent
        swap_memory_used = psutil.swap_memory().used / 1024 / 1024 / 1024

        # disk usage
        disk_usage = psutil.disk_usage('/').percent

        # temperature
        cpu_temp = psutil.sensors_temperatures()['cpu_thermal'][0].current

        # i/o stats
        io_stats = psutil.disk_io_counters()
        read_bytes = io_stats.read_bytes
        write_bytes = io_stats.write_bytes
        read_count = io_stats.read_count
        write_count = io_stats.write_count

        result = {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "memory_used": memory_used,
            "swap_memory_usage": swap_memory_usage,
            "swap_memory_used": swap_memory_used,
            "disk_usage": disk_usage,
            "cpu_temp": cpu_temp,
            "read_bytes": read_bytes,
            "write_bytes": write_bytes,
            "read_count": read_count,
            "write_count": write_count,
        }

        # log
        LOGGER.log_info(f"{result}")

        if ENV_DURATION is not None and time.time() - start_time > float(ENV_DURATION):
            break

        # sleep
        time.sleep(ENV_SLEEP)


if __name__ == '__main__':
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)

    if ENV_DURATION is not None and not isInteger(ENV_DURATION) and not isFloat(ENV_DURATION):
        LOGGER.log_error("Duration must be a positive number.")
        sys.exit(1)

    if not isInteger(ENV_SLEEP) and not isFloat(ENV_SLEEP):
        LOGGER.log_error("Duration and sleep must be a positive number.")
        sys.exit(1)

    ENV_SLEEP = int(ENV_SLEEP)
    ENV_DURATION = int(ENV_DURATION) if ENV_DURATION is not None else None

    run_system_information_measurement()
