FROM python:3.9-slim

# Set a working directory inside the container
WORKDIR /app

# Copy the Python script into the container
COPY /measurements/gps/gps_measurement.py /app/
COPY /helper/tinkerforge/ip_connection.py /app/helper/tinkerforge/
COPY /helper/tinkerforge/bricklet_gps_v3.py /app/helper/tinkerforge/
COPY /helper/tinkerforge/device_display_names.py /app/helper/tinkerforge/

COPY /core/utils.py /app/core/
COPY /core/logger.py /app/core/


CMD ["python", "gps_measurement.py"]
