FROM python:3.9-slim

RUN apt-get update && apt-get install -y build-essential
RUN pip install numpy pandas pyarrow --verbose
# Set a working directory inside the container
WORKDIR /app

# Create a directory for logs
RUN mkdir -p /app/exp-bricklet-voltage-current/logs
# Copy the Python script into the container
COPY /measurements/energy/energy_measurement.py /app/
COPY /helper/tinkerforge/ip_connection.py /app/helper/tinkerforge/
COPY /helper/tinkerforge/device_display_names.py /app/helper/tinkerforge/
COPY /helper/tinkerforge/bricklet_voltage_current_v2.py /app/helper/tinkerforge/

# Set the entry point to read temperature information from /sys
CMD ["python", "energy_measurement.py"]
