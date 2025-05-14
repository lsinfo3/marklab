FROM python:3.9-slim
RUN apt-get update && apt-get install -y traceroute
WORKDIR /app

COPY /core/cmd_runner.py /app/core/
COPY /core/logger.py /app/core/

COPY /measurements/traceroute/traceroute_measurment.py /app/

CMD ["python", "traceroute_measurment.py"]