FROM python:3.9-slim

RUN apt-get update && apt-get install -y tcpdump

WORKDIR /app

COPY /measurements/packet_capture/packet_capture.sh .
RUN chmod +x packet_capture.sh

ENTRYPOINT [ "./packet_capture.sh" ]