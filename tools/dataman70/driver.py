import typing as t
import logging
import time
import traceback
from tools.base_server import ABCToolDriver
from typing import Union, Optional
import serial

MAX_RETRIES = 5
# How long to wait before firing another scanned barcode to the listeners.
SCANNED_BARCODE_THROTTLE = 0.25
READ_TIMEOUT = 1


def try_utf_decode(data: Union[str,bytes]) -> str:
    if isinstance(data, str):
        return data
    data_string = ""
    try:
        data_string = data.decode("utf-8")
    except Exception:
        raise serial.SerialException(f"error decoding to utf8 string: {data!r}")
    return data_string


def serial_read(serial_port: serial.Serial) -> str:
    serial_port.reset_input_buffer()
    reply = serial_port.read_until(expected=b"\n")
    reply_string = try_utf_decode(reply)
    if reply_string == "":
        logging.warning("Dataman 70 returned empty response")
        return ""
    # The dataman 70 returns malformed responses every once in a while. Just ignore them.
    if not (reply_string[-1] == "\n" and reply_string[-2] == "\r"):
        logging.warning(f"Dataman 70 returned malformed response {reply_string}")
        return ""
    return reply_string[0:-2]


class Dataman70Driver(ABCToolDriver):
    def __init__(self, com_port: str) -> None:
        self.debug_output: bool = True
        self.serial_timeout: int = 2
        # The last barcode received.
        self.last_barcode: str = ""
        # The time the last barcode was received.
        self.last_barcode_time: Optional[float] = None
        # Listeners that will fire whenever a new barcode is received.
        self.barcode_listeners = []

        # Whether the driver is live.
        # If the driver cannot receive a signal, it will set live to False.
        # If the driver is not live, the reader_thread will halt.
        # If the driver is not live, it will be marked as disconnected via the healthcheck.
        self.live: bool = True

        # NOTE: We've seen issues where when the serial is first connected,
        # creating the serial port can take 10 seconds or more.
        # This only occurs the first time.
        self.serial_port: serial.Serial = serial.Serial(
            com_port, write_timeout=1, timeout=READ_TIMEOUT
        )

        # self.reader_thread: threading.Thread = threading.Thread(target=self.read_dataman_output)
        # self.reader_thread.daemon = True
        # self.reader_thread.start()

        # Responses from the dataman 70.
        self.responses: dict[str, t.Any] = {}

    def close(self) -> None:
        self.live = False
        self.serial_port.close()

    def process_dataman_output(self, output: str) -> None:
        if output == "":
            return

        if len(output) == 1:
            self.responses["current_trigger_type"] = output
            return

        if (
            self.last_barcode_time is None
            or time.time() - self.last_barcode_time > SCANNED_BARCODE_THROTTLE
        ):
            if self.debug_output:
                logging.info(f"Dataman detected barcode... {output}")
            self.last_barcode = output
            self.last_barcode_time = time.time()

            try:
                for listener in self.barcode_listeners:
                    listener(self.last_barcode)
            except Exception:
                logging.error(traceback.format_exc())

    def read_dataman_output(self) -> None:
        self.last_barcode = ""
        self.last_barcode_time = time.time()
        retries = 0
        while self.live:
            try:
                # Read from the Dataman.
                output = serial_read(self.serial_port)
                # # Reset retries if read is successful.
                # retries = 0

                self.process_dataman_output(output)

            except serial.SerialException:
                if self.live:
                    logging.error(traceback.format_exc())
                    retries += 1
                    time.sleep(1)

            except TypeError:
                # If not live anymore, we expect a error from read() in serial/serialposix.py.
                if not self.live:
                    pass
                else:
                    raise
            retries += 1
            # If we receive multiple errors attempting to receive data, set to disconnected.
            # We assume that if the Dataman is disconnected, this will trigger.
            if retries > MAX_RETRIES:
                self.live = False
                # read_dataman_output happens in its own thread, NOT inside the control_command decorator.
                # Oo we cannot simply raise Exception to get the instrument marked as disconnected.
                # To remedy this, we check self.live in the healthcheck.
                logging.error(
                    "Could not get valid data after multiple retries. Marking instrument as disconnected"
                )

    def power_on(self) -> None:
        self.serial_port.write(b"||>SET TRIGGER.TYPE 1\r\n")
        logging.info("Set trigger type to 1.")

    def power_off(self) -> None:
        self.serial_port.write(b"||>SET TRIGGER.TYPE 0\r\n")
        logging.info("Set trigger type to 0.")

    """
        Wait for a response, which is filled by process_dataman_output.
    """

    def _wait_for_response(self, response_type: str) -> None:
        response_retry_interval = 0.2
        max_retries = self.serial_timeout / response_retry_interval
        retries = 0
        while retries < max_retries and self.responses[response_type] is None:
            time.sleep(response_retry_interval)
            retries += 1

        # If no response is recorded, raise an error.
        if self.responses[response_type] is None:
            raise Exception(f"Timed out waiting for response {response_type}")

    # Get the on state by querying the barcode reader.
    def is_on(self) -> bool:
        # Send command
        self.responses["current_trigger_type"] = None
        self.serial_port.write(b"||>GET TRIGGER.TYPE\r\n")

        self._wait_for_response("current_trigger_type")
        if self.responses["current_trigger_type"] == "1":
            return True
        return False

    def read_barcode(self) -> str:
        if not self.live:
            raise Exception("Dataman 70 is not live")

        for retry in range(MAX_RETRIES):
            barcode = serial_read(self.serial_port)
            if barcode != "":
                return barcode

        return ""

    def register_barcode_listener(self, fn: t.Callable[[str], t.Any]) -> None:
        self.barcode_listeners.append(fn)
