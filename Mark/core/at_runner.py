import serial
import time


class ATRunner:
    wait_time = 30

    def __init__(self, port, baudrate, timeout, wait_time=30):
        self.wait_time = wait_time

        try:
            with serial.Serial(port, timeout=0.01) as ser:
                ser.read(self.ser.in_waiting or 1)  # timeout and discard input buffer
        except Exception:
            pass

        self.ser = serial.Serial(port, baudrate, timeout=timeout)

    def open(self):
        self.ser.open()

    def close(self):
        try:
            self.ser.close()
        except Exception:
            pass

    # send command and return RESPONSE
    def send_immediate(self, cmd):
        self.ser.reset_input_buffer()  # clear input buffer
        self.ser.write((cmd + '\r\n').encode())  # send command
        response = self.ser.read(self.ser.in_waiting or 1).decode('utf-8')  # read RESPONSE
        return response

    # send command and wait for RESPONSE
    def send(self, cmd):
        if self.ser.isOpen():
            self.ser.reset_input_buffer()  # clear input buffer
            self.ser.reset_output_buffer()  # clear output buffer
            self.ser.write((cmd + '\r\n').encode())  # send command

            timer = time.time() + self.wait_time  # set timer
            response = ""

            # wait for RESPONSE
            while True:
                response += self.ser.read(self.ser.in_waiting or 1).decode('utf-8')  # read RESPONSE
                if response.__contains__("ERROR\r\n"):  # check if RESPONSE is complete and error
                    break
                elif response.__contains__("OK\r\n"):
                    break
                elif time.time() > timer:  # check if timeout is reached
                    response = "ERROR: Timeout!"
                    break
                time.sleep(1)

            return response
        else:
            return "ERROR: Serial port not open!"


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if self.ser is not None:
                self.ser.close()
        except Exception:
            pass


    @staticmethod
    def format_response(response):
        response = response.replace("\r\n", "")
        response = response.replace("\n", "")
        response = response.replace("\r", "")
        return response


if __name__ == "__main__":
    with ATRunner("/dev/ttyUSB2", 115200, 1, 120) as at_runner:
        at_runner.send("AT")
