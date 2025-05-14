FROM python:3.9-slim

RUN apt-get update && apt-get install -y gcc python3-dev

RUN pip install psutil

# Set a working directory inside the container
WORKDIR /app

# Copy the Python script into the container
COPY /measurements/system_information/system_information.py /app/
COPY /core/utils.py /app/core/
COPY /core/logger.py /app/core/

# Set the entry point to read temperature information from /sys
CMD ["python", "system_information.py"]