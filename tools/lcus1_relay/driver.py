from tools.base_server import ABCToolDriver

import logging
import serial


# Hex commands for standard LCUS-1 USB Relays
# ON:  A0 01 01 A2
# OFF: A0 01 00 A1
CMD_ON = b"\xa0\x01\x01\xa2"
CMD_OFF = b"\xa0\x01\x00\xa1"


class Lcus1RelayDriver(ABCToolDriver):
    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 2.0) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    def initialize(self) -> None:
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            self.ser.flush()
            logging.info(f"Initialized LCUS-1 relay on serial port: {self.port}")
        except serial.SerialException as e:
            logging.error(f"Failed to initialize serial port: {e}")

    def close(self) -> None:
        self.ser.close()
        logging.info(f"Closed LCUS-1 relay on serial port: {self.port}")

    def on(self) -> None:
        self.ser.write(CMD_ON)
        self.ser.flush()
        logging.info(f"LCUS-1 relay on serial port: {self.port} is ON")

    def off(self) -> None:
        self.ser.write(CMD_OFF)
        self.ser.flush()
        logging.info(f"LCUS-1 relay on serial port: {self.port} is OFF")


if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.DEBUG)
    driver = Lcus1RelayDriver("/dev/cu.usbserial-110")
    try:
        driver.initialize()
        driver.on()
        time.sleep(1)
        driver.off()
    except Exception as e:
        logging.error(f"Error during LCUS-1 relay operation: {e}")
    finally:
        driver.close()
