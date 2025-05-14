import subprocess
import sys

PORTS_BY_MODEM = {
    "Quectel_EC21": {"index": 2, "expected_length": 4},
    "Quectel_BG96": {"index": 2, "expected_length": 4}
}

def find_modem_port(modem_name: str) -> str:
    try:
        completed_process = subprocess.run(
            f"udevadm info -t --path "
            f"$(udevadm info --query=property --path=/devices/platform -e --no-pager --property-match ID_MM_PHYSDEV_UID={modem_name} | grep 'DEVPATH' | cut -d '=' -f 2)"
            f" | grep -E -o 'ttyUSB[0-9]+' | sort -n | uniq",
            shell=True, check=True, capture_output=True, text=True
        )
        found_ports = completed_process.stdout.strip().split("\n")

        defined_ports = PORTS_BY_MODEM.get(modem_name)

        if defined_ports is None:
            raise Exception(f"Unknown modem {modem_name}.")

        if len(found_ports) != defined_ports["expected_length"]:
            raise Exception(f"udevadm returned unexpected number of serial ports: {len(found_ports)}, expected 4.")

        return f"/dev/{found_ports[defined_ports["index"]]}"

    except subprocess.CalledProcessError as ex:
        raise ex

if __name__ == "__main__":
    print(find_modem_port(sys.argv[1]))
