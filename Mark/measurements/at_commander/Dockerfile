FROM python:3.9-slim

RUN pip install pyserial

WORKDIR /app

COPY /core/at_runner.py /app/core/
COPY /core/at_cmds.py /app/core/
COPY /core/logger.py /app/core/

COPY /measurements/at_commander/at_commander.py /app/

CMD ["python", "at_commander.py"]