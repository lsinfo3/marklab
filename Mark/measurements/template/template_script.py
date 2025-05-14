import os

# Environment variables that are always provided by the node
ENV_DEVICE_NAME = os.environ.get('PC_NAME', "Mark1")  # Name of the node. Is provided automatically by the node
ENV_MODEM = os.environ.get('MODEM', "Quectel_BG96")  # Name of the selected modem. Is provided automatically by the node
ENV_PORT = os.environ.get('PORT', "/dev/ttyUSB2")  # Name of the selected port. Is provided automatically by the node
ENV_IP_HOST = os.environ.get('IP_HOST')  # Established IP address of the node. Is provided automatically by the node
ENV_INTERFACE = os.environ.get('INTERFACE')  # Network interface: wwan0 or wwan1. Is provided automatically by the node


# Other environment variables that are provided by the user
# ...

def run_some_s3xy_stuff():
    pass


if __name__ == '__main__':
    # optional: check if all required environment variables are set
    # Do some s3xy stuff
    run_some_s3xy_stuff()
