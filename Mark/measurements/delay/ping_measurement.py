import os
import re
from core.cmd_runner import CommandRunner
from core.logger import Logger

ENV_INTERFACE = os.environ.get('INTERFACE')  # should be wwan0
ENV_IP_TARGET = os.environ.get('IP_TARGET', "8.8.8.8")  # should be the destination ip address to ping or check
ENV_DEVICE_NAME = os.environ.get('PC_NAME')  # should be your rasp name
ENV_MODEM = os.environ.get('MODEM')  # should be Qualcomm or Quectel
ENV_COUNT = os.environ.get('COUNT', 60)  # should be the number of ping to send
ENV_INTERVAL = os.environ.get('INTERVAL', 1)  # should be the interval between each ping
ENV_LOG_PATH = os.environ.get('LOG_PATH', './logs')
# init logger
LOGGER = Logger('ping_measurement', ENV_DEVICE_NAME, ENV_MODEM, filepath=ENV_LOG_PATH, filename='ping_measurement.log')


def convert_ping_output_to_csv(ping_output):
    try:
        # split the ping output by new line
        ping_output = ping_output.split('\n')

        # create a new file with the name of the device and the date
        file_name = f"{ENV_LOG_PATH}/ping_measurement.csv"
        with open(file_name, 'w') as file:
            # first line is the header
            file.write(f"timestamp, latency, ttl, icmp_seq, ip_address\n")
            for line in ping_output:
                # check if the line contains the ping output
                if "bytes from" in line and "icmp_seq" in line and "time" in line and "ttl" in line:
                    # split the line by space
                    timestamp = re.search(r"\[(.*?)\]", line).group(1)
                    latency = re.search(r"time=(\d+(\.\d+)?)", line).group(1)
                    ttl = re.search(r"ttl=(\d+)", line).group(1)
                    icmp_seq = re.search(r"icmp_seq=(\d+)", line).group(1)
                    ip_address = re.search(r"from (.*?):", line).group(1)
                    file.write(f"{timestamp},{latency},{ttl},{icmp_seq},{ip_address}\n")
                else:
                    continue
    except Exception as e:
        LOGGER.log_error(f"Error: {str(e)} \n")


def run_ping_measurement():
    try:
        LOGGER.log_info(f"Start ping measurement on {ENV_INTERFACE} interface to {ENV_IP_TARGET}.")
        # Run the ping command and capture the output
        ping_output = CommandRunner.run(f"ping -D -i {ENV_INTERVAL} -I {ENV_INTERFACE} -c {ENV_COUNT} {ENV_IP_TARGET}")

        LOGGER.log_info(f"ping output: \n{ping_output}")

        # Parse ping output to extract latency and packet loss information
        latency_pattern = r"min/avg/max/mdev = (\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)"
        packet_loss_pattern = r"(\d+(\.\d+)?)% packet loss"

        latency_match = re.search(latency_pattern, ping_output)
        packet_loss_match = re.search(packet_loss_pattern, ping_output)

        if latency_match and packet_loss_match:
            min_latency, avg_latency, max_latency, mdev_latency = latency_match.groups()
            LOGGER.log_info(f"{min_latency},{avg_latency},{max_latency},{mdev_latency},{packet_loss_match.group(1)} \n")
            if float(packet_loss_match.group(1)) > 0:
                convert_ping_output_to_csv(ping_output)
        else:
            LOGGER.log_warning(f"0,0,0,0,100 \n")

    except Exception as e:
        LOGGER.log_error(f"Error: {str(e)} \n")


if __name__ == '__main__':

    if ENV_INTERFACE is None or ENV_INTERFACE == "" or ENV_MODEM is None or ENV_MODEM == "":
        LOGGER.log_error("Error: Missing environment variables: INTERFACE, MODEM")
        exit(1)

    run_ping_measurement()
