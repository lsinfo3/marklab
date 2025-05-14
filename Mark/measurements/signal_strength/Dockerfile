FROM python:3.9-slim

RUN pip install pyserial

WORKDIR /app

COPY /core/at_runner.py /app/core/
COPY /core/at_cmds.py /app/core/
COPY /core/logger.py /app/core/

COPY /measurements/signal_strength/signal_quality_measurement.py /app/

# Specify the Python script as the command to run
CMD ["python", "signal_quality_measurement.py"]