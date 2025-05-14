FROM python:3.9-slim

RUN apt-get update && apt-get install -y modemmanager build-essential libusb-1.0-0-dev git && rm -rf /var/lib/apt/lists/*

# Clone uhubctl and compile it
RUN git clone https://github.com/mvp/uhubctl && \
    cd uhubctl && \
    make && \
    make install

RUN pip install pyserial pyudev

WORKDIR /app

COPY /core/at_runner.py /app/core/
COPY /core/at_cmds.py /app/core/
COPY /core/logger.py /app/core/
COPY /core/runner.py /app/core/
COPY /core/uhub_runner.py /app/core/

COPY /core/cmd_runner.py /app/core/

COPY /setup/modem_controller/modem_controller.py /app/


CMD ["python", "modem_controller.py"]