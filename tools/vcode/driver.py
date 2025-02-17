
import os
import logging 
import threading 
from tools.base_server import ABCToolDriver

try:
    import pythoncom
except Exception:
    # The driver will error if there's no pythoncom
    pass

if os.name == "nt":
    import clr  # type: ignore
    SDK_DLL = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "deps",
                "AxInterop.MicroplateLabelerLib.dll",
            )

    clr.AddReference(SDK_DLL) 

    from AxMicroplateLabelerLib import AxMicroplateLabeler # type: ignore

else:
    class AxMicroplateLabeler(): # type: ignore
        def __init__(self) -> None:
            pass
    
        def Initialize(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
        
        def Close(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
        
        def HomeStage(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
        
        def PrintAndApply(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
        def PrintAndApplyByFormatName(self) -> None:
            raise NotImplementedError(
                "AxPlateLoc is not supported on non-Windows platforms"
            )
        def PrintLabelByFormatName(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )       
        def PrintLabel(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
        def ShowDiagsDialog(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
        def DropStage(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )       
        def RotateStage(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
        def Rotate180(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
        def GetLastError(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
SIDE_MAP = {
    'east':1,
    'north':2,
    'west':4,
    'south':8
}

class VCodeDriver(ABCToolDriver):
    def __init__(self , profile:str) -> None:
        self.profile: str = profile
        self.live : bool  = False
        self.client : AxMicroplateLabeler
        self.instantiate()

    def instantiate(self) -> None:
        pythoncom.CoInitialize()
        self.client = AxMicroplateLabeler()
        self.client.CreateControl()
        self.client.Blocking = True
        pythoncom.CoUninitialize()

    def initialize(self) -> None:
        args : dict = {"profile":self.profile}
        self.schedule_threaded_command("initialize", args)

    def close(self) -> None:
        self.schedule_threaded_command("close", {})
    
    def home_stage(self) -> None:
        self.schedule_threaded_command("home_stage",{})

    def print_and_apply_by_index(self, format_index:int, side:str, drop_stage:bool, field_0:str, field_1:str, field_2:str, field_3:str, field_4:str, field_5:str) -> None:
        args :dict = {
            "format_index": format_index,
            "side":int(SIDE_MAP[side]), 
            "drop_stage":drop_stage, 
            "field_0":field_0, 
            "field_1":field_1,
            "field_2":field_2,
            "field_3":field_3,
            "field_4":field_4,
            "field_5":field_5
        }
        self.schedule_threaded_command("print_and_apply", args)

    def print_and_apply_by_name(self, format_name:str, side:str, drop_stage:bool, field_0:str, field_1:str, field_2:str, field_3:str, field_4:str, field_5:str) -> None:
        args :dict = {
            "format_name": format_name,
            "side":int(SIDE_MAP[side]), 
            "drop_stage":bool(drop_stage), 
            "field_0":field_0, 
            "field_1":field_1,
            "field_2":field_2,
            "field_3":field_3,
            "field_4":field_4,
            "field_5":field_5
        }
        self.schedule_threaded_command("print_and_apply_by_name", args)

    def print_label(self, format_index:str, field_0:str, field_1:str, field_2:str, field_3:str, field_4:str, field_5:str) -> None:
        args :dict = {
            "format_index": format_index,
            "field_0":field_0, 
            "field_1":field_1,
            "field_2":field_2,
            "field_3":field_3,
            "field_4":field_4,
            "field_5":field_5
        }
        self.schedule_threaded_command("print_label", args)
    
    def show_diagnostics(self) -> None:
        self.schedule_threaded_command("show_diagnostics", {"modal":True, "level":1})
    
    def drop_stage(self, variant:bool) -> None:
         self.schedule_threaded_command("drop_stage", {"variant":variant})
    
    def rotate_stage(self, angle:float) -> None:
        self.schedule_threaded_command("rotate_stage",{"angle":angle})
    
    def rotate180(self) -> None:
        self.schedule_threaded_command("rotate_180",{})

    def schedule_threaded_command(self, command:str, arguments:dict) -> None:  # type: ignore
        self.execution_thread = threading.Thread(target=self.execute_command(command, arguments,)) # type: ignore
        self.execution_thread.daemon = True
        self.execution_thread.start()
        return None
    
    def execute_command(self, command:str, arguments:dict) -> None:
        response = 0
        try:
            if command == "initialize":
                response = self.client.Initialize(arguments["profile"])
            elif command == "close":
                response  = self.client.Close()
            elif command == "home_stage":
                response = self.client.HomeStage()
            elif command == "print_and_apply":
                response= self.client.PrintAndApply(arguments["format_index"],
                                                 arguments["side"],
                                                 arguments["drop_stage"],
                                                 arguments["field_0"],
                                                 arguments["field_1"],
                                                 arguments["field_2"],
                                                 arguments["field_3"],
                                                 arguments["field_4"],
                                                 arguments["field_5"]
                                                 )
            elif command == "print_and_apply_by_name":
                response= self.client.PrintAndApplyByFormatName(arguments["format_name"],
                                                 arguments["side"],
                                                 arguments["drop_stage"],
                                                 arguments["field_0"],
                                                 arguments["field_1"],
                                                 arguments["field_2"],
                                                 arguments["field_3"],
                                                 arguments["field_4"],
                                                 arguments["field_5"]
                                                 )
            elif command == "print_label":
                response= self.client.PrintLabelByFormatName(arguments["format_name"],
                                                 arguments["field_0"],
                                                 arguments["field_1"],
                                                 arguments["field_2"],
                                                 arguments["field_3"],
                                                 arguments["field_4"],
                                                 arguments["field_5"]
                                                 )

            elif command == "show_diagnostics":
                response = self.client.ShowDiagsDialog(arguments["modal"],arguments["level"])
            elif command == "drop_stage":
                response= self.client.DropStage(arguments["variant"])
            elif command == "rotate_stage":
                response= self.client.RotateStage(arguments["angle"])
            elif command == "rotate_180":
                response= self.client.Rotate180()
            elif command == "get_last_error":
                response= self.client.GetLastError()
            else:
                response = -1
        except RuntimeError as e:
            self.live = False
            raise RuntimeError(f"Failed to execute command {str(e)}")
        finally:
            pythoncom.CoUninitialize()
            logging.info(f"Received response is {response}")
            if(response != 0):
                error : str = self.client.GetLastError()
                raise RuntimeError(f"Failed to execute command {command} with error {error}")
            return None