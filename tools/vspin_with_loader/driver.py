
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

class VSpinWithLoader(ABCToolDriver):
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
    
    def home(self) -> None: 
        self.schedule_threaded_command("home", {})

    def close_door(self) -> None: 
        self.schedule_threaded_command("close_door",{})
    
    def validate_bucket(self, bucket:int):
        if bucket < 1 or bucket > 2:
            raise RuntimeError(f"Bucket must be either 1 or 2. Received: {bucket}")
        return True
    
    def validate_gripper_offset(self, gripper_offset:float):
        if gripper_offset < 2.6 or gripper_offset > 21.1:
            raise RuntimeError(f"Gripper offset must be between 0 and 20. Received: {gripper_offset}")
        return True
    
    def validate_plate_height(self, plate_height:float):
        if plate_height < 0.0 or plate_height > 48.0:
            raise RuntimeError(f"Plate height must be between 0 and 20. Received: {plate_height}")
        return True
    
    def validate_load_speed(self, speed_level:int):
        if speed_level < 0 or speed_level > 3:
            raise RuntimeError(f"Speed level must be between 0(slow) and 3(fast). Received: {speed_level}")
        return True
    
    def options(self, option_index):
        if option_index < 0 or option_index > 7:
            raise RuntimeError(f"The options argument should be a value between 0-7: (0) - no options set, (1) - ignore plate sensor, (2) - grip plates gently, (3) - ignore plate sensor and grip " +
                    "plates gently, (4) - assume maximum plate height (plate height argument will be ignored), (5) - assume maximum plate height and ignore plate sensor, (6) - assume maximum " +
                    "plate height and grip plates gently, (7) - use all options. Received: {option_index}")
        return True
    

    def load_plate(self, bucket_number:int, gripper_offset:float, plate_height:float, speed:int, options:int) -> None: 
        args :dict = {
            "bucket_num": bucket_number,
            "gripper_offset": gripper_offset, 
            "plate_height":plate_height, 
            "speed":speed, 
            "options":options
        }

        #Validate buckets
        self.schedule_threaded_command("load_plate", args)


    def open_door(self, bucket:int) -> None:
        if bucket < 1 or bucket > 2:
            raise RuntimeError(f"Bucket must be either 1 or 2.")
        
        args:dict = {
            "bucket_num": bucket
        }
        self.schedule_threaded_command("open_door", args)

    def park(self) -> None: 
        """ Parks the centrifuge loader. Moves the gripper head under and behind loader palte stage."""
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
        if self.validate_bucket(bucket_num_load) is False:
            raise RuntimeError(f"Invalid bucket number for loading: {bucket_num_load}")
        
        if self.validate_gripper_offset(gripper_offset_load) is False:
            raise RuntimeError(f"Invalid gripper offset for loading: {gripper_offset_load}")
        if self.validate_gripper_offset(gripper_offset_unload) is False:
            raise RuntimeError(f"Invalid gripper offset for unloading: {gripper_offset_unload}")
        if self.validate_plate_height(plate_height_load) is False:
            raise RuntimeError(f"Invalid plate height for loading: {plate_height_load}")
        if self.validate_plate_height(plate_height_unload) is False:
            raise RuntimeError(f"Invalid plate height for unloading: {plate_height_unload}")
        if self.validate_load_speed(speed_load) is False:
            raise RuntimeError(f"Invalid speed for loading: {speed_load}")
        if self.validate_load_speed(speed_unload) is False:
            raise RuntimeError(f"Invalid speed for unloading: {speed_unload}")
        
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

    def  stop_spin_cycle(self, bucket_num) -> None:
        """ Stops the current spin cycle."""
        if not self.validate_bucket(bucket_num):
            raise RuntimeError(f"Invalid bucket number: {bucket_num}")
        self.client.StopSpinCycle({"bucket_num": bucket_num})


    def unload_plate(self, bucket_num:int,
                    gripper_offset:float,
                    plate_height:float,
                    speed:int,
                    options:int) -> None:
        """ Unloads the plate from the specified bucket."""
        # Validate inputs
        if self.validate_bucket(bucket_num) is False:
            raise RuntimeError(f"Invalid bucket number: {bucket_num}")
        if self.validate_gripper_offset(gripper_offset) is False:
            raise RuntimeError(f"Invalid gripper offset: {gripper_offset}")
        if self.validate_plate_height(plate_height) is False:
            raise RuntimeError(f"Invalid plate height: {plate_height}")
        if self.validate_load_speed(speed) is False:
            raise RuntimeError(f"Invalid speed: {speed}")
        
        self.schedule_threaded_command("load_plate", {
            "bucket_num": bucket_num,
            "gripper_offset": gripper_offset,
            "plate_height": plate_height,
            "speed": speed,
            "options": options
        })

    def show_diagnostics(self) -> None:
        self.schedule_threaded_command("show_diagnostics", {"modal":True, "level":1})

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
            elif command == "home":
                response = self.client.Home()
            elif command == "close_door":
                response == self.client.CloseDoor() 
            elif command == "load_plate":
                response= self.client.LoadPlate(arguments["bucket_num"],
                                                 arguments["gripper_offset"],
                                                 arguments["plate_height"],
                                                 arguments["speed"],
                                                 arguments["options"]
                                                 )
            elif command == "show_diagnostics":
                response = self.client.ShowDiagsDialog(arguments["modal"],arguments["level"])
            elif command == "open_door":
                response= self.client.OpenDoor(arguments["bucket_num"])
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
        