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
                "AxInterop.CentrifugeLib.dll",
            )

    clr.AddReference(SDK_DLL) 

    from AxCentrifugeLib import AxCentrifuge # type: ignore

else:
    class AxCentrifuge(): # type: ignore
        def __init__(self) -> None:
            pass
        
        def CreateControl(self) -> None:
            raise NotImplementedError(
                "AxCentrifuge is not supported on non-Windows platforms"
            )
        
        def Initialize(self, profile: str) -> int:
            raise NotImplementedError(
                "AxCentrifuge is not supported on non-Windows platforms"
            )
        
        def Close(self) -> int:
            raise NotImplementedError(
                "AxCentrifuge is not supported on non-Windows platforms"
            )
        
        def Home(self) -> int:
            raise NotImplementedError(
                "AxCentrifuge is not supported on non-Windows platforms"
            )
        
        def CloseDoor(self) -> int:
            raise NotImplementedError(
                "AxCentrifuge is not supported on non-Windows platforms"
            )
        
        def OpenDoor(self, bucket_num: int) -> int:
            raise NotImplementedError(
                "AxCentrifuge is not supported on non-Windows platforms"
            )
        
        def LoadPlate(self, bucket_num: int, gripper_offset: float, plate_height: float, speed: int, options: int) -> int:
            raise NotImplementedError(
                "AxCentrifuge is not supported on non-Windows platforms"
            )
        
        def UnloadPlate(self, bucket_num: int, gripper_offset: float, plate_height: float, speed: int, options: int) -> int:
            raise NotImplementedError(
                "AxCentrifuge is not supported on non-Windows platforms"
            )
        
        def Park(self) -> int:
            raise NotImplementedError(
                "AxCentrifuge is not supported on non-Windows platforms"
            )
        
        def SpinCycle(self, vel_percent: float, accel_percent: float, decel_percent: float, timer_mode: int, time: int, 
                     bucket_num_load: int, gripper_offset_load: float, gripper_offset_unload: float, 
                     plate_height_load: float, plate_height_unload: float, speed_load: int, speed_unload: int, 
                     load_options: int, unload_options: int) -> int:
            raise NotImplementedError(
                "AxCentrifuge is not supported on non-Windows platforms"
            )
        
        def StopSpinCycle(self, bucket_num: int) -> int:
            raise NotImplementedError(
                "AxCentrifuge is not supported on non-Windows platforms"
            )
        
        def ShowDiagsDialog(self, modal: bool, level: int) -> int:
            raise NotImplementedError(
                "AxCentrifuge is not supported on non-Windows platforms"
            )
        
        def GetLastError(self) -> str:
            raise NotImplementedError(
                "AxCentrifuge is not supported on non-Windows platforms"
            )
        
        @property
        def Blocking(self) -> bool:
            raise NotImplementedError(
                "AxCentrifuge is not supported on non-Windows platforms"
            )
        
        @Blocking.setter
        def Blocking(self, value: bool) -> None:
            raise NotImplementedError(
                "AxCentrifuge is not supported on non-Windows platforms"
            )

class VSpinWithLoader(ABCToolDriver):
    def __init__(self , profile:str) -> None:
        self.profile: str = profile
        self.live : bool  = False
        self.client : AxCentrifuge
        self.instantiate()

    def instantiate(self) -> None:
        pythoncom.CoInitialize()
        self.client = AxCentrifuge()
        self.client.CreateControl()
        self.client.Blocking = True
        pythoncom.CoUninitialize()

    def initialize(self) -> None:
        args : dict = {"profile":self.profile}
        self.schedule_threaded_command("initialize", args)

    def close(self) -> None:
        self.schedule_threaded_command("close", {})
    
    def home(self) -> None: 
        self.schedule_threaded_command("home", {})

    def close_door(self) -> None: 
        self.schedule_threaded_command("close_door",{})
    
    def validate_bucket(self, bucket:int) -> None:
        if bucket < 1 or bucket > 2:
            raise RuntimeError(f"Bucket must be either 1 or 2. Received: {bucket}")
        return True
    
    def validate_gripper_offset(self, gripper_offset:float) -> None:
        if gripper_offset < 2.6 or gripper_offset > 21.1:
            raise RuntimeError(f"Gripper offset must be between 2.6 and 21.1. Received: {gripper_offset}")
        return True
    
    def validate_plate_height(self, plate_height:float) -> None:
        if plate_height < 0.0 or plate_height > 48.0:
            raise RuntimeError(f"Plate height must be between 0.0 and 48.0. Received: {plate_height}")
        return True
    
    def validate_load_speed(self, speed_level:int) -> None:
        if speed_level < 0 or speed_level > 3:
            raise RuntimeError(f"Speed level must be between 0(slow) and 3(fast). Received: {speed_level}")
        return True
    
    def validate_options(self, option_index) -> None:
        if option_index < 0 or option_index > 7:
            raise RuntimeError(f"The options argument should be a value between 0-7: Received: {option_index}")
        return True
    

    def load_plate(self, bucket_number:int, gripper_offset:float, plate_height:float, speed:int, options:int) -> None: 
        # Validate inputs
        self.validate_bucket(bucket_number)
        self.validate_gripper_offset(gripper_offset)
        self.validate_plate_height(plate_height)
        self.validate_load_speed(speed)
        self.validate_options(options)
        
        args :dict = {
            "bucket_num": bucket_number,
            "gripper_offset": gripper_offset, 
            "plate_height":plate_height, 
            "speed":speed, 
            "options":options
        }
        self.schedule_threaded_command("load_plate", args)


    def open_door(self, bucket:int) -> None:
        self.validate_bucket(bucket)
        
        args:dict = {
            "bucket_num": bucket
        }
        self.schedule_threaded_command("open_door", args)

    def park(self) -> None: 
        """ Parks the centrifuge loader. Moves the gripper head under and behind loader plate stage."""
        self.schedule_threaded_command("park", {})

    def spin_cycle(self, 
                   vel_percent:float, 
                   accel_percent:float, 
                   decel_percent:float, 
                   timer_mode:int,
                   time:int, 
                   bucket_num_load:int, 
                   gripper_offset_load:float, 
                   gripper_offset_unload:float, 
                   plate_height_load:float, 
                   plate_height_unload:float, 
                   speed_load:int, 
                   speed_unload:int, 
                   load_options:int, 
                   unload_options:int) -> None:
        """ Spins the centrifuge with the specified parameters."""
        # Validate inputs
        self.validate_bucket(bucket_num_load)
        self.validate_gripper_offset(gripper_offset_load)
        self.validate_gripper_offset(gripper_offset_unload)
        self.validate_plate_height(plate_height_load)
        self.validate_plate_height(plate_height_unload)
        self.validate_load_speed(speed_load)
        self.validate_load_speed(speed_unload)
        self.validate_options(load_options)
        self.validate_options(unload_options)
        
        args:dict = {
            "vel_percent": vel_percent,
            "accel_percent": accel_percent,
            "decel_percent": decel_percent,
            "timer_mode": timer_mode,
            "time": time,
            "bucket_num_load": bucket_num_load,
            "gripper_offset_load": gripper_offset_load,
            "gripper_offset_unload": gripper_offset_unload,
            "plate_height_load": plate_height_load,
            "plate_height_unload": plate_height_unload,
            "speed_load": speed_load,
            "speed_unload": speed_unload,
            "load_options": load_options,
            "unload_options": unload_options
        }
        self.schedule_threaded_command("spin_cycle", args)

    def stop_spin_cycle(self, bucket_num:int) -> None:
        """ Stops the current spin cycle."""
        self.validate_bucket(bucket_num)
        args = {"bucket_num": bucket_num}
        self.schedule_threaded_command("stop_spin_cycle", args)

    def unload_plate(self, bucket_num:int,
                    gripper_offset:float,
                    plate_height:float,
                    speed:int,
                    options:int) -> None:
        """ Unloads the plate from the specified bucket."""
        # Validate inputs
        self.validate_bucket(bucket_num)
        self.validate_gripper_offset(gripper_offset)
        self.validate_plate_height(plate_height)
        self.validate_load_speed(speed)
        self.validate_options(options)
        
        self.schedule_threaded_command("unload_plate", {
            "bucket_num": bucket_num,
            "gripper_offset": gripper_offset,
            "plate_height": plate_height,
            "speed": speed,
            "options": options
        })

    def show_diagnostics(self, modal:bool = True, level:int = 1) -> None:
        self.schedule_threaded_command("show_diagnostics", {"modal":modal, "level":level})

    def schedule_threaded_command(self, command:str, arguments:dict) -> None:  # type: ignore
        self.execution_thread = threading.Thread(target=self.execute_command, args=(command, arguments)) # type: ignore
        self.execution_thread.daemon = True
        self.execution_thread.start()
        return None
    
    def execute_command(self, command:str, arguments:dict) -> None:
        response = 0
        try:
            pythoncom.CoInitialize()
            if command == "initialize":
                response = self.client.Initialize(arguments["profile"])
            elif command == "close":
                response = self.client.Close()
            elif command == "home":
                response = self.client.Home()
            elif command == "close_door":
                response = self.client.CloseDoor() 
            elif command == "load_plate":
                response = self.client.LoadPlate(arguments["bucket_num"],
                                                 arguments["gripper_offset"],
                                                 arguments["plate_height"],
                                                 arguments["speed"],
                                                 arguments["options"]
                                                 )
            elif command == "show_diagnostics":
                response = self.client.ShowDiagsDialog(arguments["modal"],arguments["level"])
            elif command == "open_door":
                response = self.client.OpenDoor(arguments["bucket_num"])
            elif command == "park":
                response = self.client.Park()
            elif command == "spin_cycle":
                response = self.client.SpinCycle(
                    arguments["vel_percent"],
                    arguments["accel_percent"],
                    arguments["decel_percent"],
                    arguments["timer_mode"],
                    arguments["time"],
                    arguments["bucket_num_load"],
                    arguments["gripper_offset_load"],
                    arguments["gripper_offset_unload"],
                    arguments["plate_height_load"],
                    arguments["plate_height_unload"],
                    arguments["speed_load"],
                    arguments["speed_unload"],
                    arguments["load_options"],
                    arguments["unload_options"]
                )
            elif command == "stop_spin_cycle":
                response = self.client.StopSpinCycle(arguments["bucket_num"])
            elif command == "unload_plate":
                response = self.client.UnloadPlate(arguments["bucket_num"],
                                                   arguments["gripper_offset"],
                                                   arguments["plate_height"],
                                                   arguments["speed"],
                                                   arguments["options"])
            elif command == "get_last_error":
                response = self.client.GetLastError()
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