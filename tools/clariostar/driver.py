import logging
import os
import struct
import time
from typing import cast
from dataclasses import dataclass
from enum import Enum

from tools.base_server import ABCToolDriver


class PollType(str, Enum):
    PlateOut = "PlateOut"
    Status = "Status"
    T1notreached = "T1notreached"


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
    from win32com.client.dynamic import CDispatch

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
            """
            Initialize the CLARIOstar driver.

            Args:
                device_name: Name of the ActiveX server (default: "CLARIOstar")
                            For multiple installations, use "CLARIOstar2", "CLARIOstar3", etc.
                protocol_dir: Path to the directory containing the CLARIOstar protocols. This is determined
                    in the clariostar software and cannot be configured via this driver.
                data_dir: Path specified in CLARIOstar software for mars data. This is determined
                    in the clariostar software and cannot be configured via this driver.
                output_dir: Path specified in CLARIOstar software for output data. This is determined
                    in the clariostar software and cannot be configured via this driver.

            Notes:
            To export data to a text file, this must be configured in the clariostar software via
            Settings -> Data Output -> Define Format
            Where the output_dir can be specified as well as the filename and format of the output file.
            This will enable automatic export of data to a text file after each protocol run.
            An example of filename format:
            <date:yymmdd>_<time:hhmmss>-<protocol>-<method>-<ID1>-<ID2>-<ID3>
            protocol = protocol name
            method = type of measurement, e.g. Fluorescence Intensity, Luminescence, etc.
            ID1-ID3 = user defined IDs
            """
            self.protocol_dir: str = protocol_dir
            self.data_dir: str = data_dir
            self.output_dir: str = output_dir
            self.device_name: str = device_name
            self.live: bool = False
            self.client: CDispatch

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

            # Initialize COM and create the client
            # Use CoInitializeEx with COINIT_MULTITHREADED to avoid hanging in non-GUI threads (like gRPC workers)
            # that don't pump messages.
            pythoncom.CoInitialize()
            # pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
            try:
                self.client = win32com.client.Dispatch("BMG_ActiveX.BMGRemoteControl")
                logging.info("CLARIOstar ActiveX client created successfully")
            except Exception as e:
                logging.error(f"Failed to create CLARIOstar ActiveX client: {e}")
                pythoncom.CoUninitialize()
                raise
            self.open_connection()

        def open_connection(self) -> int:
            """
            Open connection to the CLARIOstar software.

            Returns:
                0 if successful
                -1 if connection already active
                -2 if server not registered
                -3 if different server is active
            """
            logging.info(f"Opening connection to ActiveX server {self.device_name}")
            result = cast(int, self.client.OpenConnectionV(self.device_name))
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

            return result

        def close_connection(self) -> None:
            """Close the connection and terminate the CLARIOstar software."""
            self.client.CloseConnection()
            self.live = False
            logging.info("Connection closed")

        def initialize(self) -> int:
            """Initialize the reader.

            Note:
            Establishing connection automatically initializes the instrument
            so we don't need to call initialize() explicitly.
            """
            logging.info("Initializing reader")
            cmd_list = ["Init"]
            result = cast(int, self.client.Execute(cmd_list))
            logging.info(f"Reader initialized with {result}")

            logging.info("Reader initialized")
            return result

        def get_info(self, item_name: str) -> str:
            """
            Get status information from the reader.

            Args:
                item_name: Name of the information item to retrieve
                        (e.g., "Status", "PlateOut", "Temp1", etc.)

            Returns:
                String value of the requested item
            """

            result: str = cast(str, self.client.GetInfoV(item_name)).strip()

            logging.info(f"Asking clariostar about {item_name} results in: {result}")

            return result

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
                        else:
                            last_poll_times[id(criteria)] = current_time

                time.sleep(0.1)

        def execute(
            self,
            cmd: list,
        ) -> int:
            """
            Execute a command using Execute (non-blocking)
            """
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
            result = cast(int, self.client.Execute(cmd))

            if result != 0:
                logging.error(f"Command execution failed to start: {result}")
                return result

            return result

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
                        desired_result="Ready",
                        timeout=180.0,
                        poll_interval=1.0,
                    )
                ]
            )
            return 0


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    try:
        # Create driver instance
        driver = CLARIOstarDriver()

        # Move plate out
        driver.plate_out()

        # Move plate in
        driver.plate_in()

        # Close connection
        driver.close_connection()

    except Exception as e:
        print(f"Error: {e}")
