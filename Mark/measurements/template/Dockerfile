FROM python:3.9-slim

# optional: install any dependencies e.g. traceroute
# RUN apt-get update && apt-get install -y traceroute

# Set a working directory inside the container
WORKDIR /app

# Copy the Python script into the container
COPY /measurements/template/template_script.py /app/


# Run the Python script
CMD ["python", "template_script.py"]