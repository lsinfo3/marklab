FROM python:3.9-slim

RUN apt-get update && apt-get install -y modemmanager
RUN pip install pyserial

WORKDIR /app

COPY /core/at_cmds.py /app/core/
COPY /core/mmcli_cmds.py /app/core/
COPY /core/mmcli_parser.py /app/core/
COPY /core/cmd_runner.py /app/core/
COPY /core/at_runner.py /app/core/
COPY /core/logger.py /app/core/
COPY /core/json_logger.py /app/core/
COPY /core/runner.py /app/core/
COPY /setup/operator_scan/operator_scan.py /app/

CMD ["python", "operator_scan.py"]