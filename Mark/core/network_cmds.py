import re
import subprocess

from core.cmd_runner import CommandRunner


class NetworkManager:

    @classmethod
    def link_up(cls, interface):
        """
        Brings up a network interface.
        :param interface: The network interface.
        :return: True if the network interface was brought up successfully, False otherwise.
        """
        output = CommandRunner.run("ip link set " + interface + " up")
        return output

    @classmethod
    def link_down(cls, interface):
        """
        Brings down a network interface.
        :param interface: The network interface.
        :return: True if the network interface was brought down successfully, False otherwise.
        """
        output = CommandRunner.run("ip link set " + interface + " down")
        return output

    @classmethod
    def add_ip(cls, ip, interface):
        """
        Adds an IP address to a network interface.
        :param ip: The IP address.
        :param interface: The network interface.
        :return: True if the IP address was added successfully, False otherwise.
        """
        output = CommandRunner.run("ip addr add " + ip + "/32 dev " + interface)
        return output

    @classmethod
    def del_ip(cls, ip, interface):
        """
        Deletes an IP address from a network interface.
        :param ip: The IP address.
        :param interface: The network interface.
        :return: True if the IP address was deleted successfully, False otherwise.
        """
        output = CommandRunner.run("ip addr flush dev " + interface)
        return output

    @classmethod
    def get_ip_address(cls, interface="all"):
        """
        Gets the IP address of a network interface.
        :return: Show IP addresses of all network interfaces.
        """
        cmd = f"ip addr"
        if interface != "all":
            cmd += f" show {interface}"
        output = CommandRunner.run(cmd)
        return output

    # @classmethod
    # def check_interface(cls, interface):
    #     interface_addr = psutil.net_if_addrs()[interface]
    #     for addr in interface_addr:
    #         if addr.family == socket.AF_INET:
    #             return True
    #     return False

    @classmethod
    def ping_check(cls, interface, ip_target="google.com"):
        """
        Checks if an IP address can be pinged over a network interface.
        :param interface: The network interface.
        :param ip_target: The IP address to ping.
        :return: True if the IP address can be pinged successfully, False otherwise.
        """
        try:
            ping_process = subprocess.Popen(
                ["ping", "-I", interface, "-w", str(10), "-q", ip_target],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            ping_output, _ = ping_process.communicate()
            packet_loss_pattern = r"(\d+(\.\d+)?)% packet loss"
            packet_loss_match = re.search(packet_loss_pattern, ping_output)

            if packet_loss_match:
                packet_loss = float(packet_loss_match.group(1))
                success = packet_loss < 50 # 50% packet loss is acceptable
                return success, f"{packet_loss}% packet loss"

            return False, "no match in ping output"
        except Exception as e:
            return False, str(e)
