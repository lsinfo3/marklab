import psutil

from watchdog_utils import log
from time import sleep
from random import randint

import sys
sys.path.append("/home/ubuntu/mark")

from core.utils_api import send_health_check_message_to_server


def check_disk_usage():
    """
    Checks the disk usage.
    """
    return psutil.disk_usage('/')

if __name__ == '__main__':
    try:
        # Sleep for a random time (up to 2 minutes) to avoid all devices sending health checks at the same time
        sleep(randint(0, 120))
        message = "System is healthy"
        status = "online"  # possible values: online, offline, critical, maintenance
        disk_usage = check_disk_usage()
        if disk_usage.percent > 90:
            log(f"Disk usage is higher than 90%: {disk_usage.percent}", "health_check.log")
            message = "Disk usage is higher than 90%"
            status = "critical"

        try:
            r = send_health_check_message_to_server(message, status)
            log(f"Health check sent successfully: {r}", "health_check.log")

        except Exception as ex:
            log(f"Error while sending health check: {ex}", "health_check.log")
            exit(1)

    except Exception as ex:
        log(f"Error while checking system: {ex}", "health_check.log")
        exit(1)
