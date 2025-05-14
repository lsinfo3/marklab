# Use an official Python runtime as a parent image
FROM python:3.9-slim
RUN apt-get update && apt-get install -y curl
# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY /measurements/upload/upload_measurement.py /app/
COPY /core/logger.py /app/core/
COPY /core/json_logger.py /app/core/
COPY /core/cmd_runner.py /app/core/
COPY /measurements/upload/1B.txt /app/files/
COPY /measurements/upload/2B.txt /app/files/
COPY /measurements/upload/4B.txt /app/files/
COPY /measurements/upload/8B.txt /app/files/
COPY /measurements/upload/16B.txt /app/files/
COPY /measurements/upload/32B.txt /app/files/
COPY /measurements/upload/64B.txt /app/files/
COPY /measurements/upload/128B.txt /app/files/
COPY /measurements/upload/256B.txt /app/files/
COPY /measurements/upload/1KB.txt /app/files/
COPY /measurements/upload/10KB.txt /app/files/
COPY /measurements/upload/20KB.txt /app/files/
COPY /measurements/upload/30KB.txt /app/files/
COPY /measurements/upload/40KB.txt /app/files/
COPY /measurements/upload/50KB.txt /app/files/
COPY /measurements/upload/60KB.txt /app/files/
COPY /measurements/upload/70KB.txt /app/files/
COPY /measurements/upload/80KB.txt /app/files/
COPY /measurements/upload/90KB.txt /app/files/
COPY /measurements/upload/100KB.txt /app/files/
COPY /measurements/upload/200KB.txt /app/files/
COPY /measurements/upload/300KB.txt /app/files/
COPY /measurements/upload/400KB.txt /app/files/
COPY /measurements/upload/500KB.txt /app/files/
COPY /measurements/upload/600KB.txt /app/files/
COPY /measurements/upload/700KB.txt /app/files/
COPY /measurements/upload/800KB.txt /app/files/
COPY /measurements/upload/900KB.txt /app/files/
COPY /measurements/upload/1MB.txt /app/files/
COPY /measurements/upload/2MB.txt /app/files/
COPY /measurements/upload/2.5MB.txt /app/files/
COPY /measurements/upload/3MB.txt /app/files/
COPY /measurements/upload/4MB.txt /app/files/
COPY /measurements/upload/5MB.txt /app/files/

# Run the Python script when the container launches
CMD ["python", "upload_measurement.py"]


