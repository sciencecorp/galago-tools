import logging
import os
import threading
import time
from typing import Union

from tools.base_server import ABCToolDriver

try:
    import pythoncom
except Exception:
    # The driver will error if there's no pythoncom
    pass

if os.name == "nt":
    import clr  # type: ignore

    SDK_DLL = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "deps",
        "AxInterop.VSTACKBIONETLib.dll",
    )

    clr.AddReference(SDK_DLL)

    from AxVSTACKBIONETLib import AxVStackBioNet  # type: ignore

else:

    class AxVStackBioNet:  # type: ignore
        def __init__(self) -> None:
            pass

        def Initialize(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")

        def Close(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")

        def Abort(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")

        def Downstack(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")

        def Home(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")

        def Ignore(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")

        def Jog(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")

        def LoadStack(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")

        def OpenGripper(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")

        def ReleaseStack(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")

        def Retry(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")

        def SetButtonMode(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")

        def SetLabware(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")

        def ShowDiagsDialog(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")

        def Upstack(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")

        def GetLastError(self) -> None:
            raise NotImplementedError("AxVStackBioNet is not supported on non-Windows platforms")


class VStackDriver(ABCToolDriver):
    def __init__(self, profile: str) -> None:
        self.profile: str = profile
        self.live: bool = False
        self.client: AxVStackBioNet
        self.lock = threading.Lock()  # To synchronize access to the device
        self.instantiate()
        self.initialize()

    def instantiate(self) -> None:
        pythoncom.CoInitialize()
        self.client = AxVStackBioNet()
        self.client.CreateControl()
        self.client.Blocking = True
        pythoncom.CoUninitialize()

    def initialize(self) -> None:
        args: dict = {"profile": self.profile}
        self.execute_command("initialize", args)

    def close(self) -> None:
        self.schedule_threaded_command("close", {})

    def abort(self) -> None:
        self.schedule_threaded_command("abort", {})
        return

    def downstack(self) -> None:
        self.schedule_threaded_command("downstack", {})
        return

    def home(self) -> None:
        self.schedule_threaded_command("home", {})
        return

    def jog(self, increment: float) -> None:
        self.schedule_threaded_command("jog", {"increment": increment})
        return

    def load_stack(self) -> None:
        self.schedule_threaded_command("load_stack", {})
        return

    def open_gripper(self, open: bool) -> None:
        self.schedule_threaded_command("open_gripper", {"open": open})
        return

    def release_stack(self) -> None:
        self.schedule_threaded_command("release_stack", {})
        return

    def retry(self) -> None:
        self.schedule_threaded_command("retry", {})
        return

    def set_button_mode(self, run_mode: bool, reply: str) -> None:
        self.schedule_threaded_command("set_button_mode", {"run_mode": run_mode, "reply": reply})
        return

    def set_labware(self, labware: str, plate_dimension_select: int) -> None:
        self.schedule_threaded_command(
            "set_labware", {"labware": labware, "plate_dimension_select": plate_dimension_select}
        )
        return

    def show_diagnostics(self) -> None:
        self.schedule_threaded_command("show_diagnostics", {})

    def upstack(self) -> None:
        self.schedule_threaded_command("upstack", {})
        return

    def schedule_threaded_command(self, command: str, arguments: dict) -> None:
        self.execution_thread = threading.Thread(
            target=self.execute_command(  # type: ignore[func-returns-value]
                command,
                arguments,
            )
        )
        self.execution_thread.daemon = True
        self.execution_thread.start()
        return None

    def execute_command(self, command: str, arguments: dict) -> None:
        response: Union[int, tuple] = 0
        try:
            if command == "initialize":
                response = self.client.Initialize(arguments["profile"])
            elif command == "close":
                response = self.client.Close()
            elif command == "abort":
                response = self.client.Abort()
            elif command == "downstack":
                response = self.client.Downstack()
            elif command == "home":
                response = self.client.Home()
            elif command == "ignore":
                response = self.client.Ignore()
            elif command == "jog":
                response = self.client.Jog(arguments["increment"])
            elif command == "load_stack":
                response = self.client.LoadStack()
            elif command == "open_gripper":
                response = self.client.OpenGripper(arguments["open"])
            elif command == "release_stack":
                response = self.client.ReleaseStack()
            elif command == "retry":
                response = self.client.Retry()
            elif command == "set_button_mode":
                response = self.client.SetButtonMode(arguments["run_mode"], arguments["reply"])
            elif command == "set_labware":
                response = self.client.SetLabware(
                    arguments["labware"], arguments["plate_dimension_select"]
                )
            elif command == "show_diagnostics":
                response = self.client.ShowDiagsDialog(True, 0)
            elif command == "upstack":
                response = self.client.Upstack()
            else:
                response = -1
        except RuntimeError as e:
            self.live = False
            raise RuntimeError(f"Failed to execute command {str(e)}")
        finally:
            time.sleep(1)
            pythoncom.CoUninitialize()
            logging.info(f"Received response is {response}")
            logging.info(f"Response type is {type(response)}")
            error: str = ""
            if isinstance(response, tuple):
                if response[0] != 0:
                    error = self.client.GetLastError()
                    raise RuntimeError(f"Failed to execute command {error}")
            elif isinstance(response, int):
                if response != 0:
                    error = self.client.GetLastError()
                    raise RuntimeError(f"Failed to execute command {error}")
            return None
