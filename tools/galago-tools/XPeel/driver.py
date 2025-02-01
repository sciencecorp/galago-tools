import serial
import time
import logging
from tools.base_server import ABCToolDriver

def try_ascii_decode(data: bytes) -> str:
    try:
        return data.decode("ascii")
    except Exception as e:
        raise serial.SerialException(f"ASCII decode error: {data!r} - {e}")

def serial_read(serial_port: serial.Serial) -> str:
    reply = serial_port.read_until(expected=b"\r\n")
    reply_string = try_ascii_decode(reply)
    if reply_string == "":
        logging.warning("XPeel returned empty response")
        return ""
    return reply_string.strip()

class XPeelDriver(ABCToolDriver):
    def __init__(self,com_port: str) -> None:
        self.serial_port = serial.Serial(
            com_port, 9600, timeout=1, parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS
        )
        self.write("*stat")
        self.wait_for_ready()

    def write(self, command: str) -> None:
        self.serial_port.write((command + "\r\n").encode("ascii"))

    def read(self, strict: bool = True, max_attempts: int = 10) -> str:
        attempt = 0
        while attempt < max_attempts:
            reply_string = serial_read(self.serial_port)
            if reply_string == "":
                attempt += 1
                logging.info(f"Retrying...Attempt {attempt}")
                continue
            return reply_string
        if strict:
            raise serial.SerialException("No valid data received, may have disconnected.")
        return ''

    def wait_for_ready(self) -> None:
        """ Wait until the device sends a ready message indicating it can accept new commands. """
        while True:
            response = self.read(strict=False)
            logging.info(f"Received response from xpeel: {response}")
            if response.startswith("*ready"):
                return
            time.sleep(0.1)  # short delay to prevent flooding the serial port

    def remove_seal(self) -> None:
        """ Perform a deseal operation with specific parameters. """
        self.write("*xpeel:41")
        self.wait_for_ready()

    def check_status(self) -> str:
        """ Request current status and error codes. """
        self.write("*stat")
        return self.read()

    def reset(self) -> None:
        """ Reset the device to a known good state. """
        self.write("*reset")
        self.wait_for_ready()

    def restart(self) -> None:
        """ Restart the device. """
        self.write("*restart")
        self.wait_for_ready()

    def check_tape_remaining(self) -> str:
        """ Check how much tape is left on the spools. """
        self.write("*tapeleft")
        return self.read()

    def move_conveyor_in(self) -> None:
        """ Move the conveyor in to the default begin peel position. """
        self.write("*movein")
        self.wait_for_ready()

    def move_conveyor_out(self) -> None:
        """ Move the conveyor out. """
        self.write("*moveout")
        self.wait_for_ready()

    def move_elevator_up(self) -> None:
        """ Move the elevator up. """
        self.write("*moveup")
        self.wait_for_ready()

    def move_elevator_down(self) -> None:
        """ Move the elevator down. """
        self.write("*movedown")
        self.wait_for_ready()

    def move_spool(self) -> None:
        """ Advance the spool by 10mm of tape. """
        self.write("*movespool")
        self.wait_for_ready()

    def setup_plate_check(self, enable: bool) -> None:
        """ Enable or disable plate check feature. """
        on_off = 'y' if enable else 'n'
        self.write(f"*platecheck:{on_off}")
        self.wait_for_ready()

    def close(self) -> None:
        self.serial_port.close()
