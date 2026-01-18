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
        "AxInterop.AgilentLabwareMiniHubLib.dll",
    )

    clr.AddReference(SDK_DLL)

    from AxAgilentLabwareMiniHubLib import AxLabwareMiniHubActiveX  # type: ignore

else:

    class AxLabwareMiniHubActiveX:  # type: ignore
        def __init__(self) -> None:
            pass

        def Initialize(self) -> None:
            raise NotImplementedError(
                "AxLabwareMiniHubActiveX is not supported on non-Windows platforms"
            )

        def Close(self) -> None:
            raise NotImplementedError(
                "AxLabwareMiniHubActiveX is not supported on non-Windows platforms"
            )

        def Abort(self) -> None:
            raise NotImplementedError(
                "AxLabwareMiniHubActiveX is not supported on non-Windows platforms"
            )

        def DisableMotor(self) -> None:
            raise NotImplementedError(
                "AxLabwareMiniHubActiveX is not supported on non-Windows platforms"
            )

        def EnableMotor(self) -> None:
            raise NotImplementedError(
                "AxLabwareMiniHubActiveX is not supported on non-Windows platforms"
            )

        def Jog(self) -> None:
            raise NotImplementedError(
                "AxLabwareMiniHubActiveX is not supported on non-Windows platforms"
            )

        def RotateToCassette(self) -> None:
            raise NotImplementedError(
                "AxLabwareMiniHubActiveX is not supported on non-Windows platforms"
            )

        def RotateToDegree(self) -> None:
            raise NotImplementedError(
                "AxLabwareMiniHubActiveX is not supported on non-Windows platforms"
            )

        def RotateToHomePosition(self) -> None:
            raise NotImplementedError(
                "AxLabwareMiniHubActiveX is not supported on non-Windows platforms"
            )

        def SetSpeed(self) -> None:
            raise NotImplementedError(
                "AxLabwareMiniHubActiveX is not supported on non-Windows platforms"
            )

        def ShowDiagsDialog(self) -> None:
            raise NotImplementedError(
                "AxLabwareMiniHubActiveX is not supported on non-Windows platforms"
            )

        def TeachHome(self) -> None:
            raise NotImplementedError(
                "AxLabwareMiniHubActiveX is not supported on non-Windows platforms"
            )

        def GetLastError(self) -> None:
            raise NotImplementedError(
                "AxLabwareMiniHubActiveX is not supported on non-Windows platforms"
            )


class MiniHubDriver(ABCToolDriver):
    def __init__(self, profile: str) -> None:
        self.profile: str = profile
        self.live: bool = False
        self.client: AxLabwareMiniHubActiveX
        self.lock = threading.Lock()  # To synchronize access to the device
        self.instantiate()
        self.initialize()

    def instantiate(self) -> None:
        pythoncom.CoInitialize()
        self.client = AxLabwareMiniHubActiveX()
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

    def disable_motor(self) -> None:
        self.schedule_threaded_command("disable_motor", {})
        return

    def enable_motor(self) -> None:
        self.schedule_threaded_command("enable_motor", {})
        return

    def jog(self, degree: float, clockwise: bool) -> None:
        self.schedule_threaded_command("jog", {"degree": degree, "clockwise": clockwise})
        return

    def rotate_to_cassette(self, cassette_index: int) -> None:
        self.schedule_threaded_command("rotate_to_cassette", {"cassette_index": cassette_index})
        return

    def rotate_to_degree(self, degree: float) -> None:
        self.schedule_threaded_command("rotate_to_degree", {"degree": degree})
        return

    def rotate_to_home_position(self) -> None:
        self.schedule_threaded_command("rotate_to_home_position", {})
        return

    def set_speed(self, speed: int) -> None:
        self.schedule_threaded_command("set_speed", {"speed": speed})
        return

    def show_diagnostics(self) -> None:
        self.schedule_threaded_command("show_diagnostics", {})

    def teach_home(self) -> None:
        self.schedule_threaded_command("teach_home", {})
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
            elif command == "disable_motor":
                response = self.client.DisableMotor()
            elif command == "enable_motor":
                response = self.client.EnableMotor()
            elif command == "jog":
                response = self.client.Jog(arguments["degree"], arguments["clockwise"])
            elif command == "rotate_to_cassette":
                response = self.client.RotateToCassette(arguments["cassette_index"])
            elif command == "rotate_to_degree":
                response = self.client.RotateToDegree(arguments["degree"])
            elif command == "rotate_to_home_position":
                response = self.client.RotateToHomePosition()
            elif command == "set_speed":
                response = self.client.SetSpeed(arguments["speed"])
            elif command == "show_diagnostics":
                response = self.client.ShowDiagsDialog(True, 0)
            elif command == "teach_home":
                response = self.client.TeachHome()
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
