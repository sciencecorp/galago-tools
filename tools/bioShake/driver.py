import serial
import time
import queue
import threading
import concurrent.futures
import logging
import typing as t

from tools.base_server import ABCToolDriver


class BioshakeDriver(ABCToolDriver):
    def __init__(self, port: str = "COM7"):
        """Initialize the driver with given parameters."""
        self.port: str = port
        self.ser: t.Optional[serial.Serial] = None
        self.command_queue: queue.Queue = queue.Queue()
        self.lock: threading.Lock = threading.Lock()

        # Start the command processing thread
        self.command_thread: threading.Thread = threading.Thread(
            target=self._process_commands, daemon=True
        )
        self.command_thread.start()

    def _process_commands(self) -> None:
        """Process commands from the queue asynchronously."""
        while True:
            command, expected_response, future = self.command_queue.get()
            self.write(command)
            # pause to let the device process the command and prepare a response
            time.sleep(0.1)
            response = self.read()
            if expected_response and response != expected_response:
                logging.error(f"Unexpected response for command {command}: {response}")
            # if a future object is associated with this command, set the result
            if future is not None:
                future.set_result(response)
            self.command_queue.task_done()

    def connect(self) -> None:
        """Connect to the device and test the communication."""
        if self.ser is not None and self.ser.is_open:
            logging.warning("Already connected to the device...")
            return None
        for i in range(3):
            try:
                self.ser = serial.Serial(port=self.port, baudrate=9600, timeout=1)
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
                if self.get_version() != "1.8.00":
                    logging.error("Communication test failed during connect")
                    raise Exception("Communication test failed during connect")
                logging.info("Connected to the device.")
                return None
            except Exception as e:
                logging.error(f"Attempt {i}: connection failed: {e}")
                self.disconnect()
                time.sleep(3)
        raise Exception("Unable to connect to device after several attempts")

    def disconnect(self) -> None:
        """Disconnect from the device."""
        if self.ser:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.ser.close()
        logging.info("Disconnected from the device.")

    def write(self, command: str) -> None:
        """Write a command to the device."""
        with self.lock:
            if self.ser:
                self.ser.write((command + "\r").encode())
                logging.info(f"Wrote command to the bioshaker: {command}")

    def read(self) -> t.Optional[str]:
        """Read a response from the device, strip trailing whitespace."""
        with self.lock:
            if self.ser:
                response = self.ser.readline().decode().strip()
                logging.info(f"Read response from the bioshaker: {response}")
                return response
        return None

    def query(
        self, command: str, expected_response: t.Optional[str]
    ) -> concurrent.futures.Future[str]:
        """Queue a command to the device and specify the expected response."""
        future = concurrent.futures.Future()
        self.command_queue.put((command, expected_response, future))
        return future

    def get_version(self) -> str:
        """Return the firmware version of the device."""
        future: concurrent.futures.Future[str] = self.query("getVersion", None)
        # get the result from the Future when it's available
        return future.result()

    def set_elm_lock_pos(self) -> None:
        """Close the ELM, ready for shaking."""
        self.query("setElmLockPos", "ok")

    def set_elm_unlock_pos(self) -> None:
        """Open the ELM for gripping microplates."""
        self.query("setElmUnlockPos", "ok")

    def get_elm_state_as_string(self) -> str:
        """Read out the ELM status."""
        future: concurrent.futures.Future[str] = self.query("getElmStateAsString", None)
        # get the result from the Future when it's available
        return future.result()

    def get_shake_state_as_string(self) -> str:
        """Return the state of shaking."""
        future: concurrent.futures.Future[str] = self.query(
            "getShakeStateAsString", None
        )
        # get the result from the Future when it's available
        return future.result()

    def set_shake_target_speed(self, rpm: int) -> None:
        """Set the target mixing speed in rpm."""
        self.query(f"setShakeTargetSpeed{rpm}", "ok")

    def shake_on_with_runtime(self, seconds: int) -> None:
        """Start the shaking with the current mixing speed for a defined time."""
        self.query(f"shakeOnWithRuntime{seconds}", "ok")

    def shake_on(self) -> None:
        """Start the shaking with the current mixing speed indefinitely."""
        self.query("shakeOn", "ok")

    def shake_off(self) -> None:
        """Stop the shaking, proceed to the homing position and lock in place."""
        self.query("shakeOff", "ok")

    def reset_device(self) -> None:
        """Restart the device. This takes about 30 seconds."""
        self.query("resetDevice", None)
        time.sleep(30)  # wait for the device to restart
        attempts: int = 0
        while attempts < 5:
            try:
                if self.ser:
                    self.disconnect()
                    self.ser.open()
                    if self.get_version() == "1.8.00":
                        logging.info("Communication test passed after reset")
                        break
                else:
                    self.connect()
                    logging.info("Communication test passed after reset")
                    break
                raise Exception
            except Exception:
                logging.error(
                    f"Attempt {attempts}: Communication test failed after reset"
                )
                attempts += 1
                time.sleep(10)

    def get_shake_remaining_time(self) -> int:
        """Return the remaining shaking time in seconds."""
        future: concurrent.futures.Future[str] = self.query(
            "getShakeRemainingTime", None
        )
        # get the result from the Future when it's available
        return int(future.result())

    def shake_go_home(self) -> None:
        """Shaker moves to the homing zero position and locks in place."""
        self.query("shakeGoHome", "ok")

    def __del__(self) -> None:
        """Disconnect from the device when the driver is destroyed."""
        self.disconnect()


if __name__ == "__main__":
    try:
        logging.basicConfig(
            level=logging.DEBUG,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            format="%(asctime)s - %(levelname)s - %(message)s",  # Set the log message format
        )
        driver = BioshakeDriver(port="COM7")
        driver.connect()
        print("version: ", driver.get_version())
        print("ELM state: ", driver.get_elm_state_as_string())
        print("locing...")
        driver.set_elm_lock_pos()
        print("Shake state: ", driver.get_shake_state_as_string())
        print("setting target speed to 200...")
        driver.set_shake_target_speed(rpm=200)
        print("start shaking for 10 seconds...")
        driver.shake_on_with_runtime(seconds=10)
        for i in range(5):
            print("Remaining time: ", driver.get_shake_remaining_time())
            time.sleep(1)
        print("stop shaking...")
        driver.shake_off()
        shake_state = driver.get_shake_state_as_string()
        print("Shake state: ", shake_state)
        if shake_state == "ELMLocked":
            print("unlocking...")
            driver.set_elm_unlock_pos()
        print("resetting device...")
        driver.reset_device()
    finally:
        driver.disconnect()
