import logging
import time
from tools.base_server import ABCToolDriver
import serial

class ALPS3000Driver(ABCToolDriver):
    def __init__(self, profile: str, port: str, baudrate: int = 9600, timeout: int = 1) -> None:
        self.profile: str = profile
        self.live: bool = False
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.client : serial.Serial
        self.initialize()

    def initialize(self) -> None:
        self.client = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        return None
    
    def send_command(self, command: str) -> None:
        self.client.write(f"{command}\r".encode())
        time.sleep(0.1)
        try:
            response = self.client.readline().decode().strip()
            if response != "ok" and response != "ff":
                raise RuntimeError(f"Failed to execute command: {response}")
        except RuntimeError as e:
            self.live = False
            logging.error(f"Failed to execute command {str(e)}")
        
    def close(self) -> None:
        if self.client:
            self.client.close()

    def get_status(self) -> None:
        return self.send_command("?")

    def seal_plate(self) -> None:
        self.send_command("S")

    def get_error(self) -> None:
        return self.send_command("E")

    def set_sealing_temperature(self, temperature: int) -> None:
        if 0 <= temperature <= 999:
            return self.send_command(f"A{temperature:03d}")
        else:
            raise IndexError("Temperature out of range ")

    def set_sealing_time(self, time_10ths: int) -> None:
        if 0 <= time_10ths <= 99:
            self.send_command(f"B{time_10ths:02d}")
        else:
            raise IndexError("Time out of range ")

    def get_sealing_temperature_setpoint(self) -> None:
        return self.send_command("C")

    def get_sealing_time(self) -> None:
        return self.send_command("D")

    def get_sealing_temperature_actual(self) -> None:
        return self.send_command("F")
