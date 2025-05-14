# Use an official Python runtime as a parent image
FROM python:3.9-slim
RUN apt-get update && apt-get install -y curl
# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY /core/json_logger.py /app/core/
COPY /core/cmd_runner.py /app/core/
COPY /measurements/curl_ip_address/ip_address_curl.py /app/

# Run the Python script when the container launches
CMD ["python", "ip_address_curl.py"]
