# Use an official Python runtime as a parent image
FROM python:3.9-slim

RUN apt-get update && apt-get install -y iputils-ping
# Set the working directory in the container
WORKDIR /app

RUN mkdir -p /app/logs

# Copy the current directory contents into the container at /app
COPY /measurements/delay/ping_measurement.py /app/
COPY /core/logger.py /app/core/
COPY /core/cmd_runner.py /app/core/

# Install any needed packages specified in requirements.txt
# If you have any dependencies, add them to requirements.txt and uncomment the next line
# RUN pip install -r requirements.txt

# Run the Python script when the container launches
CMD ["python", "ping_measurement.py"]


