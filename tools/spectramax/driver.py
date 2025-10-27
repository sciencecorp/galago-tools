import typing as t
import subprocess
import logging
import time
import os
from tools.base_server import ABCToolDriver
import threading
import queue
import traceback
from typing import Optional 

if os.name == "nt":
    import clr  # type: ignore

    SOFTMAX_PRO_SDK_PATH = r"C:\Program Files (x86)\Molecular Devices\SoftMax Pro 7.1.2 Automation SDK\SoftMaxPro.AutomationClient.dll"
    clr.AddReference(SOFTMAX_PRO_SDK_PATH)  # type: ignore
    from SoftMaxPro.AutomationClient import SMPAutomationClient  # type: ignore
else:
    # Make dummy SMPAutomationClient class for non-Windows platforms to at least enable simulation mode
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

    class SMPAutomationClient:  # type: ignore
        ExportAsFormat = enum.Enum("ExportAsFormat", ["COLUMNS"])

        def __init__(self) -> None:
            self.CommandCompleted = CommandCompleted()
            self.InstrumentStatusChanged = InstrumentStatusChanged()

        def Initialize(self) -> bool:
            raise NotImplementedError(
                "SMPAutomationClient is not supported on non-Windows platforms"
            )

        def Dispose(self) -> int:
            raise NotImplementedError(
                "SMPAutomationClient is not supported on non-Windows platforms"
            )

        def OpenDrawer(self) -> int:
            raise NotImplementedError(
                "SMPAutomationClient is not supported on non-Windows platforms"
            )

        def CloseDrawer(self) -> int:
            raise NotImplementedError(
                "SMPAutomationClient is not supported on non-Windows platforms"
            )

        def GetDrawerStatus(self) -> int:
            raise NotImplementedError(
                "SMPAutomationClient is not supported on non-Windows platforms"
            )

        def GetTemperature(self) -> int:
            raise NotImplementedError(
                "SMPAutomationClient is not supported on non-Windows platforms"
            )

        def GetInstrumentStatus(self) -> int:
            raise NotImplementedError(
                "SMPAutomationClient is not supported on non-Windows platforms"
            )

        def OpenFile(self, filepath: str) -> int:
            raise NotImplementedError(
                "SMPAutomationClient is not supported on non-Windows platforms"
            )

        def StartRead(self) -> int:
            raise NotImplementedError(
                "SMPAutomationClient is not supported on non-Windows platforms"
            )

        def SaveAs(self, filepath: str) -> int:
            raise NotImplementedError(
                "SMPAutomationClient is not supported on non-Windows platforms"
            )

        def ExportAs(self, filepath: str, format: str) -> int:
            raise NotImplementedError(
                "SMPAutomationClient is not supported on non-Windows platforms"
            )

        def GetDataCopy(self) -> int:
            raise NotImplementedError(
                "SMPAutomationClient is not supported on non-Windows platforms"
            )


SOFTMAX_PRO_PATH = r"C:\Program Files (x86)\Molecular Devices\SoftMax Pro 7.1.2\SoftMaxProApp.exe"
DEFAULT_PROTOCOL_DIR = r"C:\Users\Imaging Controller\Documents\spectramax_protocols"
DEFAULT_EXPERIMENT_DIR = r"C:\Users\Imaging Controller\Documents\spectramax_experiments"


class SpectramaxDriver(ABCToolDriver):
    def __init__(
        self,
        protocol_dir: str = DEFAULT_PROTOCOL_DIR,
        experiment_dir: str = DEFAULT_EXPERIMENT_DIR,
    ) -> None:
        self.protocol_dir = protocol_dir
        self.experiment_dir = experiment_dir

        self._command_lock: threading.Lock = threading.Lock()
        self.command_queue: queue.Queue[t.Any] = queue.Queue()
        self.command_response_queue: queue.Queue[t.Any] = queue.Queue()
        self.execution_thread: Optional[threading.Thread] = None
        self.live: bool = False
        self.client: SMPAutomationClient = SMPAutomationClient()
        self.softmax_process: Optional[subprocess.Popen]= None
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
        logging.info("Starting spectramax command thread")
        try:
            self.start_softmax_pro()
            while self.live:
                while not self.command_queue.empty() > 0:
                    with self._command_lock:
                        command_obj = self.command_queue.get()
                    response = self.execute_command(
                        command_obj["command"],
                        command_obj["params"],
                    )
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

    def start_softmax_pro(self) -> None:
        if not self.connected:
            # Ignore types because STARTUPINFO is only available on Windows
            startupinfo = subprocess.STARTUPINFO()  # type: ignore
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore
            self.softmax_process = subprocess.Popen(
                SOFTMAX_PRO_PATH,
                # startupinfo=startupinfo,
                #creationflags=subprocess.CREATE_NEW_CONSOLE,  # type: ignore
            )
            tries: int = 0
            while tries < 10:
                self.connected = self.client.Initialize()
                if self.connected:
                    self.client.CommandCompleted += self.handle_command_completed
                    self.client.InstrumentStatusChanged += self.handle_instrument_status_change
                    logging.info("Started softmax pro")
                    return None
                tries += 1
                time.sleep(1)
            raise Exception("Failed to start softmax pro")

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

    def execute_command(
        self, command: str, args: t.Dict[str, t.Any] = {}
    ) -> t.Any:
        command_id: int
        logging.info(f"Executing command {command}")

        if command == "open_drawer":
            command_id = self.client.OpenDrawer()
                # command_response = self.wait_for_event(command_id)
        elif command ==  "close_drawer":
                command_id = self.client.CloseDrawer()
                # command_response = self.wait_for_event(command_id)
        elif command == "get_drawer_status":
                command_id = self.client.GetDrawerStatus()
                # command_response = self.wait_for_event(command_id)
        elif command == "get_temperature":
                command_id = self.client.GetTemperature()
                # command_response = self.wait_for_event(command_id)
        elif command == "get_instrument_status":
                command_id = self.client.GetInstrumentStatus()
                # command_response = self.wait_for_event(command_id)
        elif command ==  "start_experiment":
                command_id = self.client.OpenFile(
                    os.path.join(self.protocol_dir, args["protocol_file"])
                )
                command_id = self.client.StartRead()
                command_id = self.client.SaveAs(
                    os.path.join(self.experiment_dir, args["experiment_name"] + ".sda")
                )
                command_id = self.client.ExportAs(
                    os.path.join(self.experiment_dir, args["experiment_name"] + ".txt"),
                    SMPAutomationClient.ExportAsFormat.COLUMNS,
                )
                command_id = self.client.GetDataCopy()
                # command_response = self.wait_for_event(command_id)
        else :
            raise ValueError(f"Unknown command {command}")
        return command_id
    
    def wait_for_event(self, event_id: int, timeout: Optional[int]= 60) -> t.Any:
        start_time = time.time()
        while self.live:
            seconds_spent_waiting = int(time.time() - start_time)
            if timeout and seconds_spent_waiting > timeout:
                raise Exception(
                    f"Event {event_id} has timed out. Please reset the driver."
                )

            if not self.event_queue.empty() > 0:
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
            logging.debug(f"Time spent waiting for event_id {event_id}: {seconds_spent_waiting} seconds")
            time.sleep(1)

        if not self.live:
            raise Exception(
                "Spectramax driver has crashed. Please reset the driver"
            )
        return None

    def wait_for_command(self, command: str, timeout: Optional[int] = 60) -> t.Any:
        times = 0
        start_time = time.time()

        while self.live:
            seconds_spent_waiting = int(time.time() - start_time)
            if timeout and seconds_spent_waiting > timeout:
                raise Exception(
                    f"Command {command} has timed out. Please reset the driver."
                )

            if not self.command_response_queue.empty() > 0:
                with self._command_lock:
                    command_obj: dict[str, str] = self.command_response_queue.get()
                    if command_obj["command"] == command:
                        logging.info(
                            f"Command {command} has completed. Waited for {seconds_spent_waiting} seconds"
                        )
                        return command_obj["response"]
                    else:
                        logging.warning(f"Unexpected command {command_obj['command']} received")
            times += 1
            if not self.live:
                break

            if times % 60 == 0:
                logging.info(f"Waiting for Spectramax {command} command...({seconds_spent_waiting}s)")
            time.sleep(1)

        if not self.live:
            raise Exception(
                "Spectramax driver has crashed. Please reset the driver"
            )
        return None

    def open_drawer(self) -> None:
        self.schedule_command("open_drawer")
        self.wait_for_command('open_drawer')

    def close_drawer(self) -> None:
        self.schedule_command("close_drawer")
        self.wait_for_command('close_drawer')

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
        self.client.CommandCompleted -= self.handle_command_completed
        self.client.InstrumentStatusChanged -= self.handle_instrument_status_change
        self.client.Dispose()
        if self.softmax_process:
            self.softmax_process.terminate()
            self.softmax_process.wait()
            self.softmax_process = None


if __name__ == "__main__":
    sm = SpectramaxDriver()
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