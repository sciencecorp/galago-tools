import logging
import os
import struct
import time
from typing import cast

from tools.base_server import ABCToolDriver

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
            data_dir: str = "C:\\Users\\Bioteam\\Desktop\\clariostar_automated_data",
            device_name: str = "CLARIOstar",
        ) -> None:
            """
            Initialize the CLARIOstar driver.

            Args:
                device_name: Name of the ActiveX server (default: "CLARIOstar")
                            For multiple installations, use "CLARIOstar2", "CLARIOstar3", etc.
            """
            self.protocol_dir: str = protocol_dir
            self.data_dir: str = data_dir
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
            pythoncom.CoInitialize()
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
            logging.info(f"Response: {result}")

            # Wait for instrument to be ready
            self.wait_for_status("Ready")

            if result != 0:
                raise RuntimeError(f"Failed to open connection to {self.device_name}")

            return result

        def close_connection(self) -> None:
            """Close the connection and terminate the CLARIOstar software."""
            self.client.CloseConnection()
            self.live = False
            logging.info("Connection closed")

        """
            Establishing connection automatically initializes the instrument so we don't need to call initialize() explicitly.
        """

        def initialize(self) -> int:
            """Initialize the reader."""
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

            # logging.info(f"info status is {status}")
            logging.info(f"Result of Info is {result}")

            return result

        def wait_for_status(self, status: str = "Ready", timeout: float = 15.0) -> None:
            """
            Wait for the specified status to be reached.

            Args:
                status: The status to wait for (e.g., "Ready")
                timeout: Maximum time to wait in seconds

            Raises:
                TimeoutError: If the status is not reached within the timeout
            """
            start_time = time.time()
            while True:
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Status {status} not reached within {timeout} seconds")
                if self.get_info("Status") == status:
                    break
                time.sleep(0.5)

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

            logging.info("Moving plate carrier out.")
            result = cast(int, self.client.ExecuteAndWait(cmd))
            self.wait_for_status("Ready", timeout=30)
            logging.info(f"Plate carrier moved out with result {result}")
            if result != 0:
                raise RuntimeError("Failed to move plate carrier out")
            return result

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

            logging.info("Moving plate carrier in.")
            result = cast(int, self.client.ExecuteAndWait(cmd))
            self.wait_for_status("Ready", timeout=30)
            logging.info(f"Plate carrier moved in with result {result}")
            return result

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
            result = cast(int, self.client.ExecuteAndWait(cmd))
            self.wait_for_status("Ready", timeout=10)

            logging.info(f"Temperature set to {temperature}°C")

            return result

        def run_protocol(
            self,
            protocol_name: str,
            plate_id1: str = "",
            plate_id2: str = "",
            plate_id3: str = "",
        ) -> int:
            """
            Run a measurement protocol.

            Args:
                protocol_name: Name of the protocol
                protocol_path: Path to protocol definitions
                data_path: Path where measurement data will be stored
                plate_id1: Optional plate identifier
                plate_id2: Optional plate identifier
                plate_id3: Optional plate identifier

            Returns:
                0 if successful, error code otherwise
            """
            cmd = [
                "Run",
                protocol_name,
                self.protocol_dir,
                self.data_dir,
                plate_id1,
                plate_id2,
                plate_id3,
            ]

            logging.info(f"Running protocol {protocol_name}")
            # TODO: Probably change ExecuteAndWait (blocking) to Execute (non-blocking)
            result = cast(int, self.client.ExecuteAndWait(cmd))
            self.wait_for_status("Ready", 90)
            logging.info(f"Protocol {protocol_name} completed")
            return result

        def gain_well(
            self,
            protocol_name: str,
            protocol_path: str,
            column: int,
            row: int,
            target_value_a: float,
            chromatic: int = 1,
            focus_adjustment: bool = False,
        ) -> int:
            """
            Perform gain adjustment on a specific well.

            Args:
                protocol_name: Name of the protocol
                protocol_path: Path to protocol definitions
                column: Column of well to use (1-24)
                row: Row of well to use (1-16)
                target_value_a: Target value for channel A (0-100% of range)
                chromatic: Chromatic number to use (1-5)
                focus_adjustment: Whether to perform focus adjustment

            Returns:
                0 if successful, error code otherwise
            """
            cmd = [
                "GainWell",
                protocol_name,
                protocol_path,
                str(column),
                str(row),
                str(target_value_a),
                "0",  # target_value_b (not used for CLARIOstar)
                str(chromatic),
                "0",  # target polarization (not used here)
                "A" if focus_adjustment else "-",
            ]
            logging.info(f"Executing command: {cmd}")
            result = cast(int, self.client.ExecuteAndWait(cmd))
            time.sleep(0.1)
            self.wait_for_status("Ready")
            logging.info(f"Command result: {result}")
            return result


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        # Create driver instance
        driver = CLARIOstarDriver()

        # Move plate out
        driver.plate_out()

        # Pausing to allow user to put plate on
        time.sleep(4)

        # Move plate in
        driver.plate_in()

        # Starting a test run
        driver.run_protocol(
            "Lime",
            "C:\\Program Files (x86)\\BMG\\CLARIOstar\\User\\Definit",
            "C:\\Users\\Bioteam\\Desktop\\clariostar_automated_data",
        )

        # Move plate out
        driver.plate_out()

        # Pausing to allow user to take plate out
        time.sleep(4)

        # Move plate in
        driver.plate_in()

        # Close connection
        driver.close_connection()

    except Exception as e:
        print(f"Error: {e}")
