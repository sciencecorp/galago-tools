import logging
import os
import queue
import subprocess
import threading
import time
import traceback
import typing as t
from abc import ABC, abstractmethod
from typing import Optional

from tools.base_server import ABCToolDriver

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    import clr  # type: ignore
    import win32clipboard
    import win32con

    SOFTMAX_PRO_SDK_PATH_V7 = r"C:\Program Files (x86)\Molecular Devices\SoftMax Pro 7.1.2 Automation SDK\SoftMaxPro.AutomationClient.dll"

    def load_sdk_v7():
        clr.AddReference(SOFTMAX_PRO_SDK_PATH_V7)  # type: ignore
        from SoftMaxPro.AutomationClient import SMPAutomationClient  # type: ignore

        return SMPAutomationClient
else:
    # Dummy classes for non-Windows platforms
    import enum

    class CommandCompleted:
        def __add__(self, other: t.Any) -> "CommandCompleted":
            return self

        def __sub__(self, other: t.Any) -> "CommandCompleted":
            return self

    class InstrumentStatusChanged:
        def __add__(self, other: t.Any) -> "InstrumentStatusChanged":
            return self

        def __sub__(self, other: t.Any) -> "InstrumentStatusChanged":
            return self

    class DummyAutomationClient:  # type: ignore
        ExportAsFormat = enum.Enum("ExportAsFormat", ["COLUMNS"])

        def __init__(self) -> None:
            self.CommandCompleted = CommandCompleted()
            self.InstrumentStatusChanged = InstrumentStatusChanged()

        def Initialize(self) -> bool:
            raise NotImplementedError("Not supported on non-Windows platforms")

    def load_sdk_v7():
        return DummyAutomationClient


SOFTMAX_PRO_PATH_V7 = (
    r"C:\Program Files (x86)\Molecular Devices\SoftMax Pro 7.1.2\SoftMaxProApp.exe"
)
SOFTMAX_PRO_PATH_V5 = r"C:\Program Files (x86)\Molecular Devices\SoftMax Pro 5\SoftMaxPro.exe"
DEFAULT_PROTOCOL_DIR = r"C:\Users\Imaging Controller\Documents\spectramax_protocols"
DEFAULT_EXPERIMENT_DIR = r"C:\Users\Imaging Controller\Documents\spectramax_experiments"


class SpectramaxAPIAdapter(ABC):
    """Abstract base class for different SoftMax Pro API versions"""

    @abstractmethod
    def initialize(self) -> bool:
        pass

    @abstractmethod
    def dispose(self) -> None:
        pass

    @abstractmethod
    def open_drawer(self) -> int:
        pass

    @abstractmethod
    def close_drawer(self) -> int:
        pass

    @abstractmethod
    def get_drawer_status(self) -> int:
        pass

    @abstractmethod
    def get_temperature(self) -> int:
        pass

    @abstractmethod
    def get_instrument_status(self) -> int:
        pass

    @abstractmethod
    def open_file(self, filepath: str) -> int:
        pass

    @abstractmethod
    def start_read(self) -> int:
        pass

    @abstractmethod
    def save_as(self, filepath: str) -> int:
        pass

    @abstractmethod
    def export_as(self, filepath: str, format: t.Any) -> int:
        pass

    @abstractmethod
    def get_data_copy(self) -> int:
        pass

    @abstractmethod
    def setup_event_handlers(self, command_handler: t.Callable, status_handler: t.Callable) -> None:
        pass

    @abstractmethod
    def remove_event_handlers(
        self, command_handler: t.Callable, status_handler: t.Callable
    ) -> None:
        pass


class SMP7Adapter(SpectramaxAPIAdapter):
    """Adapter for SoftMax Pro 7+ API"""

    def __init__(self, client_class):
        self.client = client_class()

    def initialize(self) -> bool:
        return self.client.Initialize()

    def dispose(self) -> None:
        self.client.Dispose()

    def open_drawer(self) -> int:
        return self.client.OpenDrawer()

    def close_drawer(self) -> int:
        return self.client.CloseDrawer()

    def get_drawer_status(self) -> int:
        return self.client.GetDrawerStatus()

    def get_temperature(self) -> int:
        return self.client.GetTemperature()

    def get_instrument_status(self) -> int:
        return self.client.GetInstrumentStatus()

    def open_file(self, filepath: str) -> int:
        return self.client.OpenFile(filepath)

    def start_read(self) -> int:
        return self.client.StartRead()

    def save_as(self, filepath: str) -> int:
        return self.client.SaveAs(filepath)

    def export_as(self, filepath: str, format: t.Any) -> int:
        return self.client.ExportAs(filepath, format)

    def get_data_copy(self) -> int:
        return self.client.GetDataCopy()

    def setup_event_handlers(self, command_handler: t.Callable, status_handler: t.Callable) -> None:
        self.client.CommandCompleted += command_handler
        self.client.InstrumentStatusChanged += status_handler

    def remove_event_handlers(
        self, command_handler: t.Callable, status_handler: t.Callable
    ) -> None:
        self.client.CommandCompleted -= command_handler
        self.client.InstrumentStatusChanged -= status_handler

    def get_export_format(self):
        return self.client.ExportAsFormat.COLUMNS


class SMP5Adapter(SpectramaxAPIAdapter):
    """Adapter for SoftMax Pro 5 and below using Windows messaging (remote control)"""

    WM_SETTEXT = 12
    SOFTMAX_WINDOW = "SOFTmax Pro"
    SOFTMAX_CLASS = "SOFTMaxPROMainWnd"
    SOFTMAX_MSG = "SOFTMaxPROMsg"

    def __init__(self, executable_path: str):
        self.executable_path = executable_path
        self.hwnd = None
        self.softmax_msg_id = None
        self._command_id_counter = 0
        self._last_status_response = ""

        # Set up Windows API functions
        if os.name == "nt":
            self.user32 = ctypes.windll.user32
            self.FindWindowW = self.user32.FindWindowW
            self.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
            self.FindWindowW.restype = wintypes.HWND

            self.SendMessageW = self.user32.SendMessageW
            self.SendMessageW.argtypes = [
                wintypes.HWND,
                wintypes.UINT,
                wintypes.WPARAM,
                wintypes.LPCWSTR,
            ]
            self.SendMessageW.restype = wintypes.LPARAM

            self.RegisterWindowMessageW = self.user32.RegisterWindowMessageW
            self.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
            self.RegisterWindowMessageW.restype = wintypes.UINT

    def _get_next_command_id(self) -> int:
        self._command_id_counter += 1
        return self._command_id_counter

    def _find_window(self) -> bool:
        """Find the SoftMax Pro window handle"""
        if os.name != "nt":
            return False
        self.hwnd = self.FindWindowW(self.SOFTMAX_CLASS, self.SOFTMAX_WINDOW)
        return self.hwnd != 0

    def _register_message(self) -> bool:
        """Register the SoftMax Pro message"""
        if self.softmax_msg_id is None:
            self.softmax_msg_id = self.RegisterWindowMessageW(self.SOFTMAX_MSG)
        return self.softmax_msg_id != 0

    def _send_command(self, command: str, wait_for_response: bool = False) -> str:
        """Send a remote command to SoftMax Pro using WM_SETTEXT approach"""
        if not self._find_window():
            raise Exception("SoftMax Pro window not found")

        if not self._register_message():
            raise Exception("Failed to register SoftMax Pro message")

        logging.debug(f"Sending command to SMP5: {command}")

        # Send the command using WM_SETTEXT
        result = self.SendMessageW(self.hwnd, self.WM_SETTEXT, self.softmax_msg_id, command)

        # Commands that return data put it on the clipboard
        if command in ["ReturnStatus", "ReturnData", "ReturnTiming"] or command.startswith(
            "Drawer"
        ):
            time.sleep(0.5)  # Brief wait for clipboard
            try:
                win32clipboard.OpenClipboard()
                data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                win32clipboard.CloseClipboard()
                response = data.decode("utf-8") if isinstance(data, bytes) else str(data)
                logging.debug(f"Got clipboard response: {response[:100]}...")
                return response
            except Exception as e:
                logging.warning(f"Failed to get clipboard data: {e}")
                win32clipboard.CloseClipboard()
                return ""

        # For non-data commands, add delay between commands
        time.sleep(0.2)
        return ""

    def _wait_until_idle(self, timeout: int = 60) -> bool:
        """Poll ReturnStatus until instrument is idle"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self._send_command("ReturnStatus")
            if "State:" in status:
                if "Idle" in status:
                    return True
                elif "Busy" in status:
                    time.sleep(2)
                    continue
                elif "Offline" in status:
                    raise Exception("SMP Status is Offline")
            time.sleep(1)
        raise Exception(f"Timeout waiting for instrument to be idle")

    def initialize(self) -> bool:
        """Launch SoftMax Pro if not running and verify connection"""
        if not self._find_window():
            logging.info("SoftMax Pro not running, launching...")
            subprocess.Popen(self.executable_path)

            # Wait for window to appear (up to 20 seconds)
            for i in range(20):
                time.sleep(1)
                if self._find_window():
                    logging.info("SoftMax Pro window found")
                    break
            else:
                logging.error("Failed to find SoftMax Pro window after launch")
                return False

        # Verify we can communicate
        if not self._register_message():
            return False

        # Test communication with ReturnStatus
        try:
            status = self._send_command("ReturnStatus")
            logging.info(
                f"SoftMax Pro 5 initialized, status: {status[:100] if status else 'no response'}"
            )
            return len(status) > 0
        except Exception as e:
            logging.error(f"Failed to communicate with SoftMax Pro: {e}")
            return False

    def dispose(self) -> None:
        """Send Close command to SoftMax Pro"""
        try:
            if self._find_window():
                self._send_command("Close")
        except:
            pass

    def open_drawer(self) -> int:
        self._send_command("OpenDrawer")
        self._wait_until_idle()
        return self._get_next_command_id()

    def close_drawer(self) -> int:
        self._send_command("CloseDrawer")
        self._wait_until_idle()
        return self._get_next_command_id()

    def get_drawer_status(self) -> int:
        self._last_status_response = self._send_command("Drawer")
        return self._get_next_command_id()

    def get_temperature(self) -> int:
        self._last_status_response = self._send_command("ReturnStatus")
        return self._get_next_command_id()

    def get_instrument_status(self) -> int:
        self._last_status_response = self._send_command("ReturnStatus")
        return self._get_next_command_id()

    def open_file(self, filepath: str) -> int:
        # Extract protocol name without extension
        protocol_name = os.path.splitext(os.path.basename(filepath))[0]
        self._send_command(f"OpenAssay:{protocol_name}")
        return self._get_next_command_id()

    def start_read(self) -> int:
        self._send_command("Read")
        self._wait_until_idle()
        return self._get_next_command_id()

    def save_as(self, filepath: str) -> int:
        self._send_command(f"SaveAs:{filepath}")
        return self._get_next_command_id()

    def export_as(self, filepath: str, format: t.Any) -> int:
        self._send_command(f"ExportAs:{filepath}")
        return self._get_next_command_id()

    def get_data_copy(self) -> int:
        self._last_status_response = self._send_command("ReturnData")
        return self._get_next_command_id()

    def setup_event_handlers(self, command_handler: t.Callable, status_handler: t.Callable) -> None:
        # SMP5 doesn't use event handlers - uses polling instead
        pass

    def remove_event_handlers(
        self, command_handler: t.Callable, status_handler: t.Callable
    ) -> None:
        pass

    def get_export_format(self):
        return None

    def parse_status_response(self, response_type: str) -> t.Any:
        """Parse the last status response for specific information"""
        if not self._last_status_response:
            return None

        import re

        if response_type == "drawer":
            # Response format: "Drawer:<tab>[Open or Closed]"
            match = re.search(r"Drawer:\s*(Open|Closed)", self._last_status_response)
            return match.group(1) if match else "Unknown"

        elif response_type == "temperature":
            # Response format: "Temperature:<tab>XXX"
            match = re.search(r"Temperature:\s*(\d+\.?\d*)", self._last_status_response)
            return float(match.group(1)) if match else 0.0

        elif response_type == "state":
            # Response format: "State:<tab>[Offline, Busy, or Idle]"
            match = re.search(r"State:\s*(\w+)", self._last_status_response)
            return match.group(1) if match else "Unknown"

        return None


class SpectramaxDriver(ABCToolDriver):
    def __init__(
        self,
        protocol_dir: str = DEFAULT_PROTOCOL_DIR,
        experiment_dir: str = DEFAULT_EXPERIMENT_DIR,
        version: int = 7,
        smp5_executable_path: str = SOFTMAX_PRO_PATH_V5,
    ) -> None:
        self.protocol_dir = protocol_dir
        self.experiment_dir = experiment_dir
        self.version = version

        self._command_lock: threading.Lock = threading.Lock()
        self.command_queue: queue.Queue[t.Any] = queue.Queue()
        self.command_response_queue: queue.Queue[t.Any] = queue.Queue()
        self.execution_thread: Optional[threading.Thread] = None
        self.live: bool = False

        # Create appropriate adapter based on version
        if version >= 7:
            if os.name == "nt":
                client_class = load_sdk_v7()
                self.adapter: SpectramaxAPIAdapter = SMP7Adapter(client_class)
            else:
                raise NotImplementedError("SMP7 only supported on Windows")
            self.softmax_path = SOFTMAX_PRO_PATH_V7
        else:
            # SMP5 uses Windows messaging, not .NET DLL
            self.adapter = SMP5Adapter(smp5_executable_path)
            self.softmax_path = smp5_executable_path

        self.softmax_process: Optional[subprocess.Popen] = None
        self.connected: bool = False
        self.instrument_status: str = "Unknown"
        self._event_lock: threading.Lock = threading.Lock()
        self.event_queue: queue.Queue[t.Any] = queue.Queue()

    def start(self) -> None:
        self.live = True
        self.execution_thread = threading.Thread(target=self.execute_spectramax_commands)
        self.execution_thread.daemon = True
        self.execution_thread.start()
        return None

    def execute_spectramax_commands(self) -> None:
        logging.info(f"Starting spectramax command thread (version {self.version})")
        try:
            self.start_softmax_pro()
            while self.live:
                while not self.command_queue.empty():
                    with self._command_lock:
                        command_obj = self.command_queue.get()
                    response = self.execute_command(
                        command_obj["command"],
                        command_obj["params"],
                    )

                    # For SMP5, create simulated event with parsed data
                    if self.version < 7:
                        event = self._create_simulated_event_smp5(response, command_obj["command"])
                    else:
                        event = self.wait_for_event(response)

                    with self._command_lock:
                        self.command_response_queue.put(
                            {"command": command_obj["command"], "response": event}
                        )
        except Exception:
            logging.warning("Spectramax command thread has errored")
            logging.error(traceback.format_exc())
            self.live = False
        return None

    def _create_simulated_event_smp5(self, command_id: int, command: str) -> t.Any:
        """Create a simulated event for SMP5 with parsed response data"""

        class SimulatedEvent:
            def __init__(
                self, cmd_id: int, string_result: str = "Completed", double_result: float = 0.0
            ):
                self.QueueID = cmd_id
                self.StringResult = string_result
                self.DoubleResult = double_result

        # Parse the response based on command type
        if isinstance(self.adapter, SMP5Adapter):
            if command == "get_drawer_status":
                result = self.adapter.parse_status_response("drawer")
                return SimulatedEvent(command_id, str(result))
            elif command == "get_temperature":
                result = self.adapter.parse_status_response("temperature")
                return SimulatedEvent(command_id, double_result=result)
            elif command == "get_instrument_status":
                result = self.adapter.parse_status_response("state")
                return SimulatedEvent(command_id, str(result))

        return SimulatedEvent(command_id)

    def start_softmax_pro(self) -> None:
        if not self.connected:
            if self.version >= 7:
                # SMP7: Launch process and initialize via .NET
                startupinfo = subprocess.STARTUPINFO()  # type: ignore
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore
                self.softmax_process = subprocess.Popen(self.softmax_path)

                tries: int = 0
                while tries < 10:
                    self.connected = self.adapter.initialize()
                    if self.connected:
                        self.adapter.setup_event_handlers(
                            self.handle_command_completed, self.handle_instrument_status_change
                        )
                        logging.info(f"Started SoftMax Pro (version {self.version})")
                        return None
                    tries += 1
                    time.sleep(1)
            else:
                # SMP5: Adapter handles process launch via Windows messaging
                self.connected = self.adapter.initialize()
                if self.connected:
                    logging.info(f"Started SoftMax Pro (version {self.version})")
                    return None

            raise Exception("Failed to start SoftMax Pro")

    def handle_command_completed(self, sender: t.Any, event: t.Any) -> None:
        logging.info(f"Command {event.QueueID} completed")
        with self._event_lock:
            self.event_queue.put({"event_id": event.QueueID, "event": event})

    def handle_instrument_status_change(self, sender: t.Any, event: t.Any) -> None:
        logging.info(f"Status change: {event.Status}")
        self.instrument_status = event.Status

    def schedule_command(self, command: str, params: dict[str, t.Any] = {}) -> None:
        logging.info(f"Scheduling command {command}, {params}")
        with self._command_lock:
            self.command_queue.put({"command": command, "params": params})

    def execute_command(self, command: str, args: t.Dict[str, t.Any] = {}) -> t.Any:
        command_id: int
        logging.info(f"Executing command {command}")

        if command == "open_drawer":
            command_id = self.adapter.open_drawer()
        elif command == "close_drawer":
            command_id = self.adapter.close_drawer()
        elif command == "get_drawer_status":
            command_id = self.adapter.get_drawer_status()
        elif command == "get_temperature":
            command_id = self.adapter.get_temperature()
        elif command == "get_instrument_status":
            command_id = self.adapter.get_instrument_status()
        elif command == "start_experiment":
            command_id = self.adapter.open_file(
                os.path.join(self.protocol_dir, args["protocol_file"])
            )
            command_id = self.adapter.start_read()
            command_id = self.adapter.save_as(
                os.path.join(self.experiment_dir, args["experiment_name"] + ".sda")
            )
            export_format = self.adapter.get_export_format()
            command_id = self.adapter.export_as(
                os.path.join(self.experiment_dir, args["experiment_name"] + ".txt"),
                export_format,
            )
            command_id = self.adapter.get_data_copy()
        else:
            raise ValueError(f"Unknown command {command}")
        return command_id

    def wait_for_event(self, event_id: int, timeout: Optional[int] = 60) -> t.Any:
        start_time = time.time()
        while self.live:
            seconds_spent_waiting = int(time.time() - start_time)
            if timeout and seconds_spent_waiting > timeout:
                raise Exception(f"Event {event_id} has timed out. Please reset the driver.")

            if not self.event_queue.empty():
                with self._event_lock:
                    event_obj: dict[str, t.Any] = self.event_queue.get()
                    if event_obj["event_id"] == event_id:
                        logging.info(
                            f"Event {event_id} has completed. Waited for {seconds_spent_waiting} seconds"
                        )
                        return event_obj["event"]
                    else:
                        logging.warning(f"Unexpected command {event_obj['event_id']} received")
            if not self.live:
                break
            logging.debug(
                f"Time spent waiting for event_id {event_id}: {seconds_spent_waiting} seconds"
            )
            time.sleep(1)

        if not self.live:
            raise Exception("Spectramax driver has crashed. Please reset the driver")
        return None

    def wait_for_command(self, command: str, timeout: Optional[int] = 60) -> t.Any:
        start_time = time.time()

        while self.live:
            seconds_spent_waiting = int(time.time() - start_time)
            if timeout and seconds_spent_waiting > timeout:
                raise Exception(f"Command {command} has timed out. Please reset the driver.")

            if not self.command_response_queue.empty():
                with self._command_lock:
                    command_obj: dict[str, str] = self.command_response_queue.get()
                    if command_obj["command"] == command:
                        logging.info(
                            f"Command {command} has completed. Waited for {seconds_spent_waiting} seconds"
                        )
                        return command_obj["response"]
                    else:
                        logging.warning(f"Unexpected command {command_obj['command']} received")

            if not self.live:
                break

            if seconds_spent_waiting % 60 == 0 and seconds_spent_waiting > 0:
                logging.info(
                    f"Waiting for Spectramax {command} command...({seconds_spent_waiting}s)"
                )
            time.sleep(1)

        if not self.live:
            raise Exception("Spectramax driver has crashed. Please reset the driver")
        return None

    def open_drawer(self) -> None:
        self.schedule_command("open_drawer")
        self.wait_for_command("open_drawer")

    def close_drawer(self) -> None:
        self.schedule_command("close_drawer")
        self.wait_for_command("close_drawer")

    def get_drawer_status(self) -> str:
        self.schedule_command("get_drawer_status")
        event = self.wait_for_command("get_drawer_status")
        return str(event.StringResult)

    def get_temperature(self) -> float:
        self.schedule_command("get_temperature")
        event = self.wait_for_command("get_temperature")
        return float(event.DoubleResult)

    def get_instrument_status(self) -> str:
        self.schedule_command("get_instrument_status")
        event = self.wait_for_command("get_instrument_status")
        return str(event.StringResult)

    def verify_reader_communication(self) -> None:
        reader_state: str = self.get_instrument_status()

        if reader_state != "Idle":
            raise Exception(f"Expected reader state Idle. Got reader state: {reader_state}")

    def start_experiment(
        self, experiment_name: str, protocol_file: str = "96wellblk_OD600_A1.spr"
    ) -> str:
        self.schedule_command(
            command="start_experiment",
            params={"experiment_name": experiment_name, "protocol_file": protocol_file},
        )
        event = self.wait_for_command("start_experiment")
        return str(event.StringResult)

    def close(self) -> None:
        self.live = False
        if self.execution_thread:
            self.execution_thread.join()

        if self.version >= 7:
            self.adapter.remove_event_handlers(
                self.handle_command_completed, self.handle_instrument_status_change
            )

        self.adapter.dispose()

        if self.softmax_process:
            self.softmax_process.terminate()
            self.softmax_process.wait()
            self.softmax_process = None


if __name__ == "__main__":
    # Test with version 5
    logging.basicConfig(level=logging.DEBUG)
    sm = SpectramaxDriver(version=5)
    try:
        print("Status: ", sm.instrument_status)
        sm.start()
        print(sm.get_instrument_status())
        print(sm.get_temperature())
        print(sm.get_drawer_status())
        sm.open_drawer()
        sm.close_drawer()
    finally:
        sm.close()
