import os
import logging 
import threading 
import time
from tools.base_server import ABCToolDriver
from typing import Union
try:
    import pythoncom
except Exception:
    pass


if os.name == "nt":
    import clr  # type: ignore
    SDK_DLL = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "deps",
                "AxInterop.Centrifuge.dll",
            )
    clr.AddReference(SDK_DLL) 
    from AxCentrifugeLib import AxCentrifuge # type: ignore

else:
    # Stub for non-Windows
    class AxCentrifuge(): # type: ignore
        def __init__(self) -> None:
            pass
        
        def Initialize(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
        
        def ShowDiagsDialog(self, modal: bool, level: int) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
            
        def Close(self) -> int:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
            
        def Home(self) -> int:
             raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
            
        def CloseDoor(self) -> int:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
            
        def OpenDoor(self) -> int:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
            
        def SpinCycle(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
            
        def StopSpinCycle(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
            
        def GetLastError(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
            
        
class VSpin(ABCToolDriver):
    def __init__(self, profile: str) -> None:
        self.profile: str = profile
        self.live: bool = False
        self.client: AxCentrifuge
        self.instantiate()

    def instantiate(self) -> None:
        pythoncom.CoInitialize()
        time.sleep(0.5)
        self.client = AxCentrifuge()
        self.client.CreateControl()
        self.client.Blocking = True
        pythoncom.CoUninitialize()

    def initialize(self) -> None: 
        args : dict = {"profile":self.profile}
        self.schedule_threaded_command("initialize", args)
    
    def close(self) -> None:
        self.schedule_threaded_command("close", {})

    def show_diagnostics(self) -> None:
        self.schedule_threaded_command("show_diagnostics",{"modal":True, "level":1})
    
    def home(self) -> None:
        self.schedule_threaded_command("home", {})

    def close_door(self) -> None:
        self.schedule_threaded_command("close_door", {})
    
    def open_door(self, bucket_number:int) -> None:
        self.schedule_threaded_command("open_door", {"bucket_number": bucket_number})

    def spin(self, 
                   time: int,
                   velocity_percent: float,
                   acceleration_percent: float,
                   decel_percent: float, 
                   timer_mode: int,
                   bucket: int,
                   ) -> None:
        """
          Runs a spin cycle. 

          Args:
                time: int - Time in seconds to spin. Max is 86400 (24 hours).
                velocity_percent: float - Speed as a percentage of max speed (0-100).
                acceleration_percent: float - Acceleration as a percentage of max (0-100).
                decel_percent: float - Deceleration as a percentage of max (0-100).
                timer_mode: int - 0 = Entire duration, 1 = Timed at full speed, 2 = Spin continuously until stopped.
                bucket: int - Which bucket to present after spin cycle finishes (1-2).
        """
        #Validate time. 
        if not (1 < time < 86400):
            raise ValueError("Time must be between 1 and 86400 seconds (24 hours).")
        
        """Spins the centrifuge with the specified parameters."""
        args : dict = {
            "velocity_percent": velocity_percent,
            "acceleration_percent": acceleration_percent,
            "deceleration_percent": decel_percent,
            "timer_mode": timer_mode,
            "time": time,
            "bucket_number": bucket,
        }

        logging.info(f"Starting spin cycle - velocity: {velocity_percent}%, time: {time}s, bucket: {bucket}")
        self.schedule_threaded_command("spin", args)

    def stop_spin(self, bucket_num: int) -> None:
        """Stops the current spin cycle."""
        logging.info("Stopping current spin cycle")
        self.schedule_threaded_command("stop_spin", {"bucket_number": bucket_num})

    def schedule_threaded_command(self, command:str, arguments:dict) -> None:  # type: ignore
        self.execution_thread = threading.Thread(target=self.execute_command(command, arguments,)) # type: ignore
        self.execution_thread.daemon = True
        self.execution_thread.start()
        return None

    def execute_command(self, command:str, arguments:dict) -> None:
        response : Union[int, tuple] = 0
        try:
            if command == "initialize":
                response = self.client.Initialize(arguments["profile"])
            elif command == "close":
                response  = self.client.Close()
            elif command == "close_door":
                response = self.client.CloseDoor()
            elif command == "open_door":
                response=  self.client.OpenDoor(arguments["bucket_number"])
            elif command == "home":
                response = self.client.Home()
            elif command == "spin":
                response = self.client.SpinCycle(
                    arguments["velocity_percent"],
                    arguments["acceleration_percent"],
                    arguments["deceleration_percent"],
                    arguments["timer_mode"],
                    arguments["time"],
                    arguments["bucket_number"],
                )
            elif command == "stop_spin":
                response = self.client.StopSpinCycle(arguments["bucket_number"])
            elif command == "get_last_error":
                response = self.client.GetLastError()
            elif command == "show_diagnostics":
                response = self.client.ShowDiagsDialog(arguments["modal"],arguments["level"])
            else:
                response = -1
        except RuntimeError as e:
            self.live = False
            raise RuntimeError(f"Failed to execute command {str(e)}")
        finally:
            time.sleep(1)
            pythoncom.CoUninitialize()
            logging.info(f"Received response is {response}")
            error : str = ""
            if isinstance(response, tuple):
                if response[0] != 0:
                    error = self.client.GetLastError()
                    raise RuntimeError(f"Failed to execute command {error}")
            elif isinstance(response, int):
                if response != 0:
                    error = self.client.GetLastError()
                    raise RuntimeError(f"Failed to execute command {error}")
            return None
        