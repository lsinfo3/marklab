FROM python:3.9-slim

RUN pip install pyserial

WORKDIR /app

COPY /core/at_runner.py /app/core/
COPY /core/at_cmds.py /app/core/
COPY /core/json_logger.py /app/core/

COPY /measurements/network_report/network_report.py /app/

CMD ["python", "network_report.py"]

