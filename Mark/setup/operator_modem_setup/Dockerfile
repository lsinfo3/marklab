FROM python:3.9-slim

RUN apt-get update && apt-get install -y modemmanager iproute2 iputils-ping build-essential libusb-1.0-0-dev git && rm -rf /var/lib/apt/lists/*

# Clone uhubctl and compile it
RUN git clone https://github.com/mvp/uhubctl && \
    cd uhubctl && \
    make && \
    make install

RUN pip install pyserial pyudev
# Set a working directory inside the container
WORKDIR /app

# Copy the Python script into the container
COPY /core/cmd_runner.py /app/core/
COPY /core/mmcli_cmds.py /app/core/
COPY /core/mmcli_parser.py /app/core/
COPY /core/network_cmds.py /app/core/
COPY /core/runner.py /app/core/
COPY /core/logger.py /app/core/
COPY /core/json_logger.py /app/core/
COPY /core/at_cmds.py /app/core/
COPY /core/at_runner.py /app/core/
COPY /core/uhub_runner.py /app/core/
COPY /setup/operator_modem_setup/operator_modem_setup.py /app/
COPY /setup/operator_modem_setup/operator_modem_core.py /app/
# Specify the Python script as the command to run
CMD ["python", "operator_modem_setup.py"]

