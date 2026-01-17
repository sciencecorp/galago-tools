import os
import logging 
import threading 
import time
from tools.base_server import ABCToolDriver
from typing import Union, Tuple

try:
    import pythoncom
except Exception:
    pass

if os.name == "nt":
    import clr  # type: ignore
    SDK_DLL = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "deps",
                "AxInterop.BenchCelLib.dll",
            )
    clr.AddReference(SDK_DLL) 
    from AxBenchCelLib import AxBenchCel  # type: ignore
else:
    class AxBenchCel():  # type: ignore
        def __init__(self) -> None:
            pass
    
        def Initialize(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
        
        def Close(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
        
        def PickAndPlace(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
        
        def Delid(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def Relid(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def LoadStack(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def ReleaseStack(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def OpenClamp(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def IsStackLoaded(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def IsPlatePresent(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def SetLabware(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def GetStackCount(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def GetTeachpointNames(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def GetLabwareNames(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def ProtocolStart(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def ProtocolFinish(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def MoveToHomePosition(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def Pause(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def Unpause(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def GetLastError(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def ShowDiagsDialog(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def ShowLabwareEditor(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def Abort(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def Retry(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )
            
        def Ignore(self) -> None:
            raise NotImplementedError(
                "AxBenchCel is not supported on non-Windows platforms"
            )

class BenchCelDriver(ABCToolDriver):
    def __init__(self, profile: str) -> None:
        self.profile: str = profile
        self.live: bool = False
        self.client: AxBenchCel
        self.lock = threading.Lock()
        self.instantiate()
        self.initialize()

    def instantiate(self) -> None:
        pythoncom.CoInitialize()
        self.client = AxBenchCel()
        self.client.CreateControl()
        self.client.Blocking = True
        pythoncom.CoUninitialize()

    def initialize(self) -> None: 
        args: dict = {"profile": self.profile}
        self.execute_command("initialize", args)
    
    def close(self) -> None:
        self.schedule_threaded_command("close", {})
    
    def pick_and_place(self, pick_from: str, place_to: str, lidded: bool, retraction_code: int) -> None:
        self.schedule_threaded_command("pick_and_place", {
            "pick_from": pick_from,
            "place_to": place_to,
            "lidded": lidded,
            "retraction_code": retraction_code
        })
    
    def delid(self, delid_from: str, delid_to: str, retraction_code: int) -> None:
        self.schedule_threaded_command("delid", {
            "delid_from": delid_from,
            "delid_to": delid_to,
            "retraction_code": retraction_code
        })
    
    def relid(self, relid_from: str, relid_to: str, retraction_code: int) -> None:
        self.schedule_threaded_command("relid", {
            "relid_from": relid_from,
            "relid_to": relid_to,
            "retraction_code": retraction_code
        })
    
    def load_stack(self, stack: int) -> None:
        self.schedule_threaded_command("load_stack", {"stack": stack})
    
    def release_stack(self, stack: int) -> None:
        self.schedule_threaded_command("release_stack", {"stack": stack})
    
    def open_clamp(self, stack: int) -> None:
        self.schedule_threaded_command("open_clamp", {"stack": stack})
    
    def is_stack_loaded(self, stack: int) -> None:
        self.schedule_threaded_command("is_stack_loaded", {"stack": stack})
    
    def is_plate_present(self, stack: int) -> None:
        self.schedule_threaded_command("is_plate_present", {"stack": stack})
    
    def set_labware(self, labware: str) -> None:
        self.schedule_threaded_command("set_labware", {"labware": labware})
    
    def get_stack_count(self) -> None:
        self.schedule_threaded_command("get_stack_count", {})
    
    def get_teachpoint_names(self) -> None:
        self.schedule_threaded_command("get_teachpoint_names", {})
    
    def get_labware_names(self) -> None:
        self.schedule_threaded_command("get_labware_names", {})
    
    def protocol_start(self) -> None:
        self.schedule_threaded_command("protocol_start", {})
    
    def protocol_finish(self) -> None:
        self.schedule_threaded_command("protocol_finish", {})
    
    def move_to_home_position(self) -> None:
        self.schedule_threaded_command("move_to_home_position", {})
    
    def pause(self) -> None:
        self.schedule_threaded_command("pause", {})
    
    def unpause(self) -> None:
        self.schedule_threaded_command("unpause", {})
    
    def show_diagnostics(self) -> None:
        self.schedule_threaded_command("show_diagnostics", {})
    
    def show_labware_editor(self, modal: bool, labware: str) -> None:
        self.schedule_threaded_command("show_labware_editor", {
            "modal": modal,
            "labware": labware
        })
    
    def abort(self) -> None:
        self.schedule_threaded_command("abort", {})
    
    def retry(self) -> None:
        self.schedule_threaded_command("retry", {})
    
    def ignore(self) -> None:
        self.schedule_threaded_command("ignore", {})

    def schedule_threaded_command(self, command: str, arguments: dict) -> None:  # type: ignore
        self.execution_thread = threading.Thread(target=self.execute_command(command, arguments,))  # type: ignore
        self.execution_thread.daemon = True
        self.execution_thread.start()
        return None

    def execute_command(self, command: str, arguments: dict) -> None:
        response: Union[int, Tuple] = 0
        try:
            if command == "initialize":
                response = self.client.Initialize(arguments["profile"])
            elif command == "pick_and_place":
                response = self.client.PickAndPlace(
                    arguments["pick_from"],
                    arguments["place_to"],
                    arguments["lidded"],
                    arguments["retraction_code"]
                )
            elif command == "delid":
                response = self.client.Delid(
                    arguments["delid_from"],
                    arguments["delid_to"],
                    arguments["retraction_code"]
                )
            elif command == "relid":
                response = self.client.Relid(
                    arguments["relid_from"],
                    arguments["relid_to"],
                    arguments["retraction_code"]
                )
            elif command == "load_stack":
                response = self.client.LoadStack(arguments["stack"])
            elif command == "release_stack":
                response = self.client.ReleaseStack(arguments["stack"])
            elif command == "open_clamp":
                response = self.client.OpenClamp(arguments["stack"])
            elif command == "is_stack_loaded":
                response = self.client.IsStackLoaded(arguments["stack"])
            elif command == "is_plate_present":
                response = self.client.IsPlatePresent(arguments["stack"])
            elif command == "set_labware":
                response = self.client.SetLabware(arguments["labware"])
            elif command == "get_stack_count":
                response = self.client.GetStackCount()
            elif command == "get_teachpoint_names":
                response = self.client.GetTeachpointNames()
            elif command == "get_labware_names":
                response = self.client.GetLabwareNames()
            elif command == "protocol_start":
                response = self.client.ProtocolStart()
            elif command == "protocol_finish":
                response = self.client.ProtocolFinish()
            elif command == "move_to_home_position":
                response = self.client.MoveToHomePosition()
            elif command == "pause":
                response = self.client.Pause()
            elif command == "unpause":
                response = self.client.Unpause()
            elif command == "show_diagnostics":
                response = self.client.ShowDiagsDialog(True, 0)
            elif command == "show_labware_editor":
                response = self.client.ShowLabwareEditor(
                    arguments["modal"],
                    arguments["labware"]
                )
            elif command == "abort":
                response = self.client.Abort()
            elif command == "retry":
                response = self.client.Retry()
            elif command == "ignore":
                response = self.client.Ignore()
            elif command == "close":
                response = self.client.Close()
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