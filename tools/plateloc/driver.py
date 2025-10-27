
import os
import logging 
import threading 
import time
from tools.base_server import ABCToolDriver
from typing import Union

try:
    import pythoncom
except Exception:
    # The driver will error if there's no pythoncom
    pass

if os.name == "nt":
    import clr  # type: ignore
    SDK_DLL = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "deps",
                "AxInterop.PlateLocLib.dll",
            )

    clr.AddReference(SDK_DLL) 

    from AxPlateLocLib import AxPlateLoc  # type: ignore

else:
    import enum 

    class AxPlateLoc():  # type: ignore
        ExportAsFormat = enum.Enum("ExportAsFormat", ["COLUMNS"])
        def __init__(self) -> None:
            pass
    
        def Initialize(self) -> None:
            raise NotImplementedError(
                "AxPlateLoc is not supported on non-Windows platforms"
            )
        
        def Close(self) -> None:
            raise NotImplementedError(
                "AxPlateLoc is not supported on non-Windows platforms"
            )
        
        def SetSealingTime(self) -> None:
            raise NotImplementedError(
                "AxPlateLoc is not supported on non-Windows platforms"
            )
        
        def SetSealingTemperature(self) -> None:
            raise NotImplementedError(
                "AxPlateLoc is not supported on non-Windows platforms"
            )
        def GetActualTemperature(self) -> None:
            raise NotImplementedError(
                "AxPlateLoc is not supported on non-Windows platforms"
            )
        def GetSealingTime(self) -> None:
            raise NotImplementedError(
                "AxPlateLoc is not supported on non-Windows platforms"
            )       
        def MoveStageIn(self) -> None:
            raise NotImplementedError(
                "AxPlateLoc is not supported on non-Windows platforms"
            )
        def MoveStageOut(self) -> None:
            raise NotImplementedError(
                "AxPlateLoc is not supported on non-Windows platforms"
            )
        def GetLastError(self) -> None:
            raise NotImplementedError(
                "AxPlateLoc is not supported on non-Windows platforms"
            )
        def ShowDiagsDialog(self) -> None:
            raise NotImplementedError(
                "AxPlateLoc is not supported on non-Windows platforms"
            )        
class PlateLocDriver(ABCToolDriver):
    def __init__(self , profile:str) -> None:
        self.profile: str = profile
        self.live : bool  = False
        self.client :AxPlateLoc
        self.lock = threading.Lock()  # To synchronize access to the device
        self.instantiate()
        self.initialize()


    def instantiate(self) -> None:
        pythoncom.CoInitialize()
        self.client = AxPlateLoc()
        self.client.CreateControl()
        self.client.Blocking = True
        pythoncom.CoUninitialize()

    def initialize(self) -> None: 
        args : dict = {"profile":self.profile}
        self.execute_command("initialize", args)
    
    def close(self) -> None:
        self.schedule_threaded_command("close", {})
    
    def seal(self) -> None:
        self.schedule_threaded_command("seal", {})
        return 
    
    def set_seal_time(self, time:float) -> None:
        self.schedule_threaded_command("set_seal_time", {"time":time})
        return 

    def set_temperature(self, temperature:float) -> None:
        self.schedule_threaded_command("set_temperature", {"temperature":temperature})
        return 
    
    def get_actual_temperature(self) -> None:
        self.schedule_threaded_command("get_actual_temperature", {})
        return 

    def stage_in(self) -> None:
        self.schedule_threaded_command("stage_in", {})
        return 
    
    def stage_out(self) -> None:
        self.schedule_threaded_command("stage_out", {})
        return 
    
    def show_diagnostics(self) -> None:
        self.schedule_threaded_command("show_diagnostics",{})

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
            elif command == "seal":
                response = self.client.ApplySeal()
            elif command == "close":
                response  = self.client.Close()
            elif command == "set_seal_time":
                response = self.client.SetSealingTime(arguments["time"])
            elif command == "set_temperature":
                response=  self.client.SetSealingTemperature(arguments["temperature"])
            elif command == "get_actual_temperature":
                response = self.client.GetActualTemperature()
            elif command == "get_seal_time":
                response = self.client.GetSealingTime()
            elif command == "stage_in":
                response = self.client.MoveStageIn()
            elif command == "stage_out":
                response = self.client.MoveStageOut()
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
            logging.info(f"Reponse type is {type(response)}")
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
