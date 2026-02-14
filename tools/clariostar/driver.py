import logging
import os
import struct
import time
import threading
import queue
from typing import Any
from dataclasses import dataclass
from enum import Enum

from tools.base_server import ABCToolDriver


class PollType(str, Enum):
    PlateOut = "PlateOut"
    Status = "Status"
    T1notreached = "T1notreached"
    MeasureData = "MeasureData"


@dataclass
class PollCriteria:
    poll_type: PollType
    desired_result: str
    timeout: float = 30.0
    poll_interval: float = 0.5


if os.name != "nt":
    raise NotImplementedError("CLARIOstar ActiveX driver is only supported on Windows platforms")
else:
    import pythoncom
    import win32com.client

    class CLARIOstarDriver(ABCToolDriver):
        """
        Python driver for BMG LABTECH CLARIOstar plate reader.
        """

        def __init__(
            self,
            protocol_dir: str = "C:\\Program Files (x86)\\BMG\\CLARIOstar\\User\\Definit",
            data_dir: str = "C:\\Program Files (x86)\\BMG\\CLARIOstar\\User\\Data",
            output_dir: str = "C:\\Program Files (x86)\\BMG\\MARS",
            device_name: str = "CLARIOstar",
        ) -> None:
            """Initialize the CLARIOstar driver."""
            self.protocol_dir: str = protocol_dir
            self.data_dir: str = data_dir
            self.output_dir: str = output_dir
            self.device_name: str = device_name
            self.live: bool = True

            # Proactively kill hanging instances to ensure a clean state
            self.kill_processes("CLARIOstar.exe", ask_user=False)
            self.kill_processes("ActiveXClient.exe", ask_user=False)

            # Thread-safety mechanisms
            self._cmd_q: queue.Queue = queue.Queue()
            self._lock = threading.Lock()

            if os.name != "nt":
                raise NotImplementedError(
                    "CLARIOstar ActiveX driver is only supported on Windows platforms"
                )

            # Check for 32-bit Python environment
            if struct.calcsize("P") * 8 != 32:
                raise RuntimeError(
                    f"CLARIOstar driver requires a 32-bit Python environment. "
                    f"Current environment is {struct.calcsize('P') * 8}-bit."
                )

            # Start worker thread
            self._worker_thread = threading.Thread(
                target=self._worker_loop, name="ClariostarWorker", daemon=True
            )
            self._worker_thread.start()
            logging.info("CLARIOstar driver initialized with dedicated worker thread")

        def _worker_loop(self) -> None:
            """Main loop for the COM worker thread."""
            pythoncom.CoInitialize()
            logging.info("COM initialized in worker thread")

            client: Any = None
            try:
                client = win32com.client.Dispatch("BMG_ActiveX.BMGRemoteControl")
                logging.info("CLARIOstar ActiveX client created in worker thread")
            except Exception as e:
                logging.error(f"Failed to create ActiveX client in worker: {e}")
                return

            while self.live:
                try:
                    # Non-blocking get to allow for 'live' check
                    item = self._cmd_q.get(timeout=1.0)
                    if item is None:
                        break

                    func_name, args, resp_q = item
                    try:
                        if func_name == "_reconnect":
                            logging.info("Worker attempting re-dispatch...")
                            client = win32com.client.Dispatch("BMG_ActiveX.BMGRemoteControl")
                            result = client.OpenConnectionV(self.device_name)
                            resp_q.put((result, None))
                            continue

                        method = getattr(client, func_name)
                        result = method(*args)
                        resp_q.put((result, None))
                    except Exception as e:
                        logging.error(f"Error executing {func_name} in worker: {e}")
                        resp_q.put((None, e))
                except queue.Empty:
                    continue
                except Exception as e:
                    logging.error(f"Unexpected error in worker loop: {e}")

            logging.info("CLARIOstar worker thread exiting")
            pythoncom.CoUninitialize()

        def _call(self, func_name: str, *args: Any, timeout: float = 30.0) -> Any:
            """Send a command to the worker thread and wait for response."""
            if not self.live:
                raise RuntimeError("Driver is not live")

            resp_q: queue.Queue = queue.Queue()
            self._cmd_q.put((func_name, args, resp_q))

            try:
                result, err = resp_q.get(timeout=timeout)
                if err:
                    raise err
                return result
            except queue.Empty:
                logging.error(f"Timeout waiting for worker response to {func_name}")
                # Try to revive if it's a timeout
                raise TimeoutError(f"Worker timeout on {func_name}")

        def open_connection(self) -> int:
            """Open connection to the CLARIOstar software."""
            logging.info(f"Opening connection to ActiveX server {self.device_name}")
            result = self._call("OpenConnectionV", self.device_name)
            logging.info(f"OpenConnectionV returned: {result}")

            self.poll_until(
                poll_criterias=[
                    PollCriteria(
                        poll_type=PollType.Status,
                        desired_result="Ready",
                        timeout=30.0,
                        poll_interval=1.0,
                    )
                ]
            )
            logging.info("Connection opened successfully")
            return int(result) if result is not None else -1

        def close_connection(self) -> None:
            """Close the connection and terminate the CLARIOstar software."""
            self._call("CloseConnection")
            self.live = False
            self._cmd_q.put(None)  # Signal worker to exit
            logging.info("Connection closed")

        def initialize(self) -> int:
            """Initialize the reader."""
            logging.info("Initializing reader")
            cmd_list = ["Init"]
            result = self._call("Execute", cmd_list)
            result_int = int(result) if result is not None else -4
            logging.info(f"Reader initialization result: {result_int}")

            if result_int == -1:
                logging.error(
                    "Connection to the reader control program has not been established -> Use OpenConnection"
                )
            if result_int == -2:
                logging.error(
                    "Connection to the reader control program has not been established -> OpenConnection was not succesful"
                )
            if result_int == -3:
                logging.error(
                    "Command could not be sent as the connection to the reader control program was lost, reopening the connection failed."
                )
            if result_int == -4:
                logging.error("Command could not be sent due to any other reason")

            return result_int

        def get_info(self, item_name: str) -> str:
            """Get status information from the reader."""
            result = self._call("GetInfoV", item_name)

            # Thread-safe recovery for empty strings
            if (result == "" or result is None) and item_name == "Status":
                logging.warning(
                    f"Empty Status detected for {item_name}, attempting thread-safe recovery..."
                )
                self._call("_reconnect")
                result = self._call("GetInfoV", item_name)

            result_str = str(result).strip() if result is not None else ""
            logging.info(f"Asking clariostar about {item_name} results in: '{result_str}'")
            return result_str

        def poll_until(self, poll_criterias: list[PollCriteria]) -> None:
            """
            Poll until the specified criteria are met.

            Args:
                poll_criteria: The criteria or list of criteria to poll for

            Raises:
                TimeoutError: If the criteria are not met within the timeout
            """
            start_time = time.time()
            last_poll_times = {id(c): 0.0 for c in poll_criterias}
            unsatisfied = poll_criterias

            while unsatisfied:
                current_time = time.time()
                # Create a copy to iterate while modifying the original list
                for criteria in unsatisfied[:]:
                    # Check timeout
                    if current_time - start_time > criteria.timeout:
                        raise TimeoutError(
                            f"Poll criteria {criteria.poll_type} not met within {criteria.timeout} seconds"
                        )

                    # Poll if interval has passed
                    if current_time - last_poll_times[id(criteria)] > criteria.poll_interval:
                        poll_result = self.get_info(criteria.poll_type.value)

                        if poll_result == criteria.desired_result:
                            unsatisfied.remove(criteria)
                        elif poll_result.lower() == "error":
                            error_message = self.get_info("Error")
                            raise RuntimeError(
                                f"Poll criteria {criteria.poll_type} resulted in error: {error_message}"
                            )
                        elif poll_result == "":
                            logging.warning(
                                f"Poll criteria {criteria.poll_type} gave empty result. "
                            )
                        else:
                            last_poll_times[id(criteria)] = current_time

                time.sleep(0.1)

        def execute(
            self,
            cmd: list,
            post_queue_delay: float = 1.0,
        ) -> int:
            """Execute a command using Execute (non-blocking) via worker thread."""
            logging.info("Checking if instrument is ready to receive command...")
            self.poll_until(
                poll_criterias=[
                    PollCriteria(
                        poll_type=PollType.Status,
                        desired_result="Ready",
                        timeout=15.0,
                        poll_interval=0.5,
                    ),
                ]
            )
            logging.info(f"Executing command: {cmd}")
            result = self._call("Execute", cmd)
            result_int = int(result) if result is not None else -4

            if result_int != 0:
                logging.error(f"Command execution failed to start: {result_int}")
                return result_int

            time.sleep(post_queue_delay)
            return result_int

        def plate_out(self, mode: str = "Normal", x: int = 0, y: int = 0) -> int:
            """
            Move plate carrier out of the instrument.

            Args:
                mode: "Normal", "Right", or "User"
                x: X coordinate for User mode (-190 to 3090)
                y: Y coordinate for User mode (4070 to 4500)

            Returns:
                0 if successful, error code otherwise
            """
            cmd = ["PlateOut", mode]
            if mode == "User":
                cmd.extend([str(x), str(y)])

            self.execute(cmd)
            self.poll_until(
                poll_criterias=[
                    PollCriteria(
                        poll_type=PollType.PlateOut,
                        desired_result="1",
                        timeout=15.0,
                        poll_interval=0.5,
                    ),
                    PollCriteria(
                        poll_type=PollType.Status,
                        desired_result="Ready",
                        timeout=15.0,
                        poll_interval=0.5,
                    ),
                ]
            )
            return 0

        def plate_in(self, mode: str = "Normal", x: int = 0, y: int = 0) -> int:
            """
            Move plate carrier into the instrument.

            Args:
                mode: "Normal" or "User"
                x: X coordinate for User mode (-190 to 3700)
                y: Y coordinate for User mode (-190 to 1590)

            Returns:
                0 if successful, error code otherwise
            """
            cmd = ["PlateIn", mode]
            if mode == "User":
                cmd.extend([str(x), str(y)])

            self.execute(cmd)
            self.poll_until(
                poll_criterias=[
                    PollCriteria(
                        poll_type=PollType.PlateOut,
                        desired_result="0",
                        timeout=15.0,
                        poll_interval=0.5,
                    ),
                    PollCriteria(
                        poll_type=PollType.Status,
                        desired_result="Ready",
                        timeout=15.0,
                        poll_interval=0.5,
                    ),
                ]
            )
            return 0

        def set_temperature(self, temperature: float) -> int:
            """
            Set the incubator temperature.

            Args:
                temperature: Target temperature in °C
                            0.0 to turn off
                            25.0-45.0 for standard incubator
                            10.0-65.0 for extended incubator

            Returns:
                0 if successful, error code otherwise
            """
            logging.info(f"Setting temperature to {temperature}°C")
            cmd = ["Temp", f"{temperature:.1f}"]
            self.execute(cmd)
            self.poll_until(
                poll_criterias=[
                    PollCriteria(
                        poll_type=PollType.T1notreached,
                        desired_result="0",
                        timeout=120.0,
                        poll_interval=2.0,
                    ),
                    PollCriteria(
                        poll_type=PollType.Status,
                        desired_result="Ready",
                        timeout=120.0,
                        poll_interval=2.0,
                    ),
                ]
            )
            return 0

        def run_protocol(
            self,
            protocol_name: str,
            plate_id: str = "",
            assay_id: str = "",
            timepoint: str = "",
        ) -> int:
            """
            Run a measurement protocol.

            Args:
                protocol_name: Name of the protocol
                protocol_path: Path to protocol definitions
                data_path: Path where measurement data will be stored
                plate_id: Optional plate identifier
                assay_id: Optional assay identifier
                timepoint: Optional timepoint identifier

            Returns:
                0 if successful, error code otherwise

            Notes:
            The plate_id, assay_id, and timepoint are given to the clariostar
            software as plate_id1, plate_id2, and plate_id3. These IDs can
            be used to name the output data file via the clariostar settings.
            """
            cmd = [
                "Run",
                protocol_name,
                self.protocol_dir,
                self.data_dir,
                plate_id,
                assay_id,
                timepoint,
            ]

            self.execute(cmd)
            self.poll_until(
                poll_criterias=[
                    PollCriteria(
                        poll_type=PollType.Status,
                        desired_result="Running",
                        timeout=180.0,
                        poll_interval=0.5,
                    ),
                ]
            )
            self.poll_until(
                poll_criterias=[
                    PollCriteria(
                        poll_type=PollType.Status,
                        desired_result="Ready",
                        timeout=180.0,
                        poll_interval=1.0,
                    ),
                    PollCriteria(
                        poll_type=PollType.MeasureData,
                        desired_result="1",
                        timeout=180.0,
                        poll_interval=1.0,
                    ),
                ]
            )
            return 0


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    try:
        # Create driver instance
        driver = CLARIOstarDriver()
        driver.open_connection()

        # Move plate out
        driver.plate_out()

        # Move plate in
        driver.plate_in()

        # Close connection
        driver.close_connection()

    except Exception as e:
        print(f"Error: {e}")
