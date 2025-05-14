FROM python:3.9-slim

RUN apt-get update && apt-get install -y hping3

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY /core/logger.py /app/core/
COPY /core/cmd_runner.py /app/core/
COPY /measurements/hping_delay/hping_measurement.py /app/

# Run the Python script when the container launches
CMD ["python", "hping_measurement.py"]