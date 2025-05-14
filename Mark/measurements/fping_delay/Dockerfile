# Use an official Python runtime as a parent image
FROM python:3.9-slim

RUN apt-get update && apt-get install -y fping

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY /core/logger.py /app/core/
COPY /core/cmd_runner.py /app/core/
COPY /measurements/fping_delay/fping_measurement.py /app/

# Run the Python script when the container launches
CMD ["python", "fping_measurement.py"]