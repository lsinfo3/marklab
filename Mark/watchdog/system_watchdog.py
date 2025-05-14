import psutil

from watchdog_utils import log

import sys
sys.path.append("/home/ubuntu/mark")

from core.utils_api import send_health_check_message_to_server


def check_cpu_usage():
    """
    Checks the cpu usage.
    """
    return psutil.cpu_percent(interval=None)


def check_memory_usage():
    """
    Checks the memory usage.
    """
    memory_usage = psutil.virtual_memory().percent
    memory_used = psutil.virtual_memory().used / 1024 / 1024 / 1024
    return memory_usage, memory_used


def check_disk_usage():
    """
    Checks the disk usage.
    """
    return psutil.disk_usage('/').percent


def check_temperature():
    """
    Checks the cpu temperature.
    :return: cpu temperature
    """
    return psutil.sensors_temperatures()['cpu_thermal'][0].current


def send_health_check(message, status):
    """
    Sends a health check to the server.
    """

    try:
        r = send_health_check_message_to_server(message, status)
        log(f"Health check sent successfully: {r}", "system_watchdog.log")
    except Exception as ex:
        log(f"Error while sending health check: {ex}", "system_watchdog.log")


if __name__ == '__main__':
    try:
        cpu_usage = check_cpu_usage()
        memory_usage, memory_used = check_memory_usage()
        disk_usage = check_disk_usage()
        cpu_temp = check_temperature()

        if cpu_usage > 85:
            log(f"CPU usage is higher than 85%: {cpu_usage}", "system_watchdog.log")
            send_health_check("CPU usage is higher than 90%", "critical")
            exit(1)
        if memory_usage > 85:
            log(f"Memory usage is higher than 85%: {memory_usage}", "system_watchdog.log")
            send_health_check("Memory usage is higher than 85%", "critical")
            exit(1)
        if disk_usage > 90:
            log(f"Disk usage is higher than 90%: {disk_usage}", "system_watchdog.log")
            send_health_check("Disk usage is higher than 90%", "critical")
            exit(1)
        if cpu_temp > 80:
            log(f"CPU temperature is higher than 80°C: {cpu_temp}", "system_watchdog.log")
            send_health_check("CPU temperature is higher than 80°C", "critical")
            exit(1)

        log("System is healthy", "system_watchdog.log")
        exit(0)
    except Exception as ex:
        log(f"Error while checking system: {ex}", "system_watchdog.log")
        exit(1)
