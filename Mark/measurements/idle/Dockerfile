FROM python:3.9-slim

# Set a working directory inside the container
WORKDIR /app

# Copy the Python script into the container
COPY /measurements/idle/idle_measurement.py /app/
COPY /core/logger.py /app/core/

# Set the entry point to read temperature information from /sys
CMD ["python", "idle_measurement.py"]