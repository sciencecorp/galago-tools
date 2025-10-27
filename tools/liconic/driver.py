import serial
import time
import logging
from tools.base_server import ABCToolDriver
import threading 
from typing import Optional, Union
from tools.app_config import Config 


ERROR_CODES = {
    "06163": "Failed to load plate. There might be a plate at specified location."
}

def try_ascii_decode(data: Union[str,bytes]) -> str:
    if isinstance(data, str):
        return data
    data_string = ""
    try:
        data_string = data.decode("ascii")
    except Exception:
        raise serial.SerialException(f"error decoding to ascii string: {data!r}")
    return data_string


def serial_read(serial_port: serial.Serial) -> str:
    reply = serial_port.read_until(expected=b"\n")
    reply_string = try_ascii_decode(reply)
    if reply_string == "":
        logging.warning("Liconic STX returned empty response")
        return ""
    # Ignore any malformed responses for now.
    if not (reply_string[-1] == "\n" and reply_string[-2] == "\r"):
        logging.warning(f"Liconic STX returned malformed response {reply_string}")
        return ""
    return reply_string[0:-2]


WAIT_TIMEOUT = 90

class LiconicStxDriver(ABCToolDriver):
    # Example: com_port can be "COM1"
    def __init__(self, com_port: str) -> None:
        self.config = Config()
        self.config.load_workcell_config()
        # if self.config.app_config.data_folder:
        #     self.co2_log_path = os.path.join(self.config.app_config.data_folder,"sensors","liconic")
        self.serial_port = serial.Serial(
            com_port, 9600, timeout=1, parity=serial.PARITY_EVEN
        )
        self.lock = threading.Lock()
        self.monitor_thread: Optional[threading.Thread] = None
        self.is_busy = False
        self.monitoring = False
        self.co2_out_of_range = False
        self.connect()

    def write(self, message: str) -> None:
        with self.lock:
            try:
                self.serial_port.write((message + "\r").encode("ascii"))
            except Exception as e:
                raise RuntimeError(f"Failed to communicate with liconic. {e}")

    # Read a single message from the serial port.
    # strict - if true, exceptions will be thrown if read fails.
    # max-attempts - number of times to retry if an empty string or error message is received.
    def read(self, strict: bool = True, max_attempts: int = 25) -> str:
        attempt = 0
        # The instruments will sometimes return an empty string or "{}" even during normal operation.
        while attempt < max_attempts:
            # Read a message.
            with self.lock:
                reply_string = serial_read(self.serial_port)

            if reply_string == "":
                attempt += 1
                logging.info(f"Retrying...Attempt {attempt}")
                continue

            # If we have reached here, the message is valid. Return it.
            return reply_string

        # If we have reached here, we have exceeded max attempts.
        # The instrument may have disconnected.
        if strict:
            raise serial.SerialException(
                f"No valid data was received. {self.serial_port.name} may have disconnected."
            )
        return ''

    def wait_for_ready(self, timeout: int = WAIT_TIMEOUT, custom_error: Optional[str]=None) -> None:
        times = 0
        while True:
            self.write("RD 1915")
            ready = self.read()
            if ready == "1":
                logging.info(f"Waited for {times} seconds")
                return
            if self.has_error():
                error_code = self.get_error_code()
                if error_code in ERROR_CODES:
                    raise Exception(f"{ERROR_CODES[error_code]}")
                else:
                    raise Exception(f"Liconic has errored with code {error_code}")
            logging.info("Liconic stx is busy. Waiting...")
            times += 1
            if times > timeout:
                raise Exception(custom_error or "Liconic has timed out waiting for command")
            time.sleep(1)

    def has_error(self) -> bool:
        self.write("RD 1814")
        return self.read() == "1"

    def get_error_code(self) -> str:
        self.write("RD DM200")
        return self.read()

    def expect_response(self, expected: str, strict: bool = False) -> None:
        response = self.read()
        if response != expected:
            if strict:
                raise Exception(f"Expected response {expected}. Got {response}")
            else:
                logging.warning(f"Expected response {expected}. Got {response}")

    def log(self, msg: str) -> None:
        logging.info(f"liconic_stx_legacy_driver: {msg}")

    def connect(self) -> None:
        self.log("Connecting...")
        self.write("CR")
        self.expect_response("CC")

    def close(self) -> None:
        self.log("Closing...")
        self.write("CQ")
        self.expect_response("CF")
        self.serial_port.close()

    def reset(self) -> None:
        self.log("Resetting...")
        self.write("ST 1900")
        self.expect_response("OK")
        self.wait_for_ready()

    def initialize(self) -> None:
        self.log("Initializing...")
        self.write("ST 1801")
        self.expect_response("OK")
        self.wait_for_ready()

    def load_plate(self, cassette: int, level: int) -> None:
        logging.info("Loading plate")
        self.is_busy = True
        try:
            self.log(f"Loading plate (cassette={cassette}, level={level})...")
            self.write(f"WR DM0 {cassette}")
            self.expect_response("OK")
            self.write(f"WR DM5 {level}")
            self.expect_response("OK")
            self.write("ST 1904")
            self.expect_response("OK")

            self.wait_for_ready()
            self.check_shovel_station_sensor("0")
            # Verify that the plate is not on the transfer station any longer.
            self.check_transfer_station_sensor("0")
        except Exception as e:
            raise RuntimeError(f"{e}")
        finally:
            self.is_busy = False
            logging.info("Loading plate complete")

    def unload_plate(self, cassette: int, level: int) -> None:
        self.is_busy = True
        try:
            self.log(f"Unloading plate (cassette={cassette}, level={level})...")
            self.write(f"WR DM0 {cassette}")
            self.expect_response("OK")
            self.write(f"WR DM5 {level}")
            self.expect_response("OK")
            self.write("ST 1905")
            self.expect_response("OK")

            self.wait_for_ready()
            self.check_shovel_station_sensor("0")
            # Verify that the plate is on the transfer station.
            self.check_transfer_station_sensor("1")
        except Exception as e:
            raise RuntimeError(f"{e}")
        finally:
            self.is_busy = False

    def read_error_code(self) -> None:
        self.write("RD DM200")
        response = self.read()
        logging.info(f"Current error code {response}")

    def check_transfer_station_sensor(self, expected: str = "0") -> None:
        self.write("RD 1813")
        self.expect_response(expected)

    def check_shovel_station_sensor(self, expected: str = "0") -> None:
        self.write("RD 1812")
        self.expect_response(expected)

    def show_cassette(self, cassette: int) -> None:
        rotate_to_cassette = (cassette - 3) % 10
        self.write(f"WR DM0 {rotate_to_cassette}")
        self.expect_response("OK")
        self.wait_for_ready()

    def raw(self, message: str) -> None:
        self.write(message)
        response = self.read()
        logging.info(f"response: {response}")

    def get_co2_set_point(self) -> str:
        self.write("RD DM894")
        return self.read()

    def set_co2_set_point(self, level: float) -> None:
        self.write(f"WR DM894 {str(int(level * 100)).zfill(5)}")
        self.expect_response("OK")

    def get_co2_cur_level(self) -> str:
        self.write("RD DM984")
        return self.read()

    def start_monitor(self) -> None:
        self.monitor_thread = threading.Thread(target=self.monitor_co2_level)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        return None

    # def write_co2_log(self, value:str) -> None:

    #     #Write to local files
    #     if self.co2_log_path is None:
    #         return
    #     if(os.path.exists(self.co2_log_path) is False):
    #         logging.debug("folder does not exist. creating folder")
    #         os.mkdir(self.co2_log_path )
    #     today =  datetime.today().strftime('%Y-%m-%d')
    #     today_folder = os.path.join(self.co2_log_path ,today)
    #     if(os.path.exists(today_folder) is False):
    #         logging.debug("folder does not exist. creating folder")
    #         os.mkdir(today_folder)
    #     trace_file = os.path.join(today_folder, "liconic_co2.txt")
    #     try:
    #         if os.path.exists(trace_file) is False:
    #             with open(trace_file, 'w+') as f:
    #                 f.write('Time,Value\n')
    #     except Exception as e:
    #         logging.debug(e)
    #         return
        
    #     try:
    #         with open(trace_file, 'a') as f:
    #             f.write(f"{datetime.today()},{value}\n")
    #     except Exception as e:
    #         logging.debug(e)
    #         return

    # def check_last_co2_level(self, data_points:int) -> Optional[int]:
    #     if self.co2_log_path is None:
    #         return
    #     today =  datetime.today().strftime('%Y-%m-%d')
    #     today_file = os.path.join(self.co2_log_path,today,"liconic_co2.txt")
    #     logging.info(today_file)
    #     if(os.path.exists(today_file) is False):
    #         logging.debug("folder does not exist.")
    #         return None 
    #     with open(today_file, "r") as f:
    #         lines = f.readlines()
    #         logging.info(F"length of lines {len(lines)}")
    #         return None

    def monitor_co2_level(self) -> None:
        self.monitoring = True
        try:
            while True:
                if not self.is_busy:
                    co2_level = float(self.get_co2_cur_level())/100
                    self.write_co2_log(str(co2_level))
                    if co2_level < 3:
                        self.co2_out_of_range = True
                        error_message = f"CO2 level is low: {co2_level}%"
                        logging.warning(error_message)
                        self.co2_out_of_range = False
                time.sleep(300)
                
        except Exception as e:
            logging.warning("Liconic monitor thread encounter an error. Restart the tool")
            logging.exception("Error is" + str(e))
            self.monitoring = False
        return None