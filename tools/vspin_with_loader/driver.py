import os
import logging 
import threading 
import time
from tools.base_server import ABCToolDriver
from typing import Union
from enum import Enum
try:
    import pythoncom
except Exception:
    pass


class LoadSpeed(Enum):
    SLOW = 1
    MEDIUM = 2
    FAST = 3

if os.name == "nt":
    import clr  # type: ignore
    SDK_DLL = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "deps",
                "AxInterop.CentrifugeLoaderLib.dll",
            )
    clr.AddReference(SDK_DLL) 
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
    
    from AxCentrifugeLoaderLib import AxCentrifugeLoader # type: ignore
    import System.Windows.Forms as WinForms  # type: ignore
    import System.Drawing as Drawing  # type: ignore

    class VSpinForm(WinForms.Form): # type: ignore
        def __init__(self) -> None:
            super().__init__()
            self.Loader
            self.form_ready = False
            self.setup_form()
            
        def setup_form(self) -> None:
            self.AutoScaleDimensions = Drawing.SizeF(6.0, 13.0)
            self.AutoScaleMode = WinForms.AutoScaleMode.Font
            self.ClientSize = Drawing.Size(284, 261)
            self.Name = "VSpinForm"
            self.Text = "VSpin Loader"
            self.WindowState = WinForms.FormWindowState.Minimized
            self.ShowInTaskbar = False
            
            # Create the ActiveX control
            self.create_loader_control()

        def create_loader_control(self) -> None:
            """Create and configure the ActiveX control"""
            try:
                self.Loader = AxCentrifugeLoader()
                self.Loader.Enabled = True
                self.Loader.Location = Drawing.Point(93, 152)
                self.Loader.Name = "axCentrifugeLoader1"
                self.Loader.Size = Drawing.Size(100, 50)
                self.Loader.TabIndex = 0
                
                # CRITICAL: Add to form controls BEFORE calling CreateControl
                self.Controls.Add(self.Loader)

                logging.info("ActiveX control created and added to form")
                
            except Exception as e:
                logging.error(f"Failed to create ActiveX control: {e}")
                raise

else:
    # Stub for non-Windows
    class AxCentrifugeLoader(): # type: ignore
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
            
        def LoadPlate(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
            
        def UnloadPlate(self) -> None:
            raise NotImplementedError(
                "AxMicroplateLabeler is not supported on non-Windows platforms"
            )
            
        def Park(self) -> None:
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
            
        @property
        def Blocking(self) -> bool:
            return False
        
        @Blocking.setter 
        def Blocking(self, value: bool) -> None:
            pass
        
    class VSpinForm: # type: ignore
        def __init__(self) -> None:
            self.Loader = AxCentrifugeLoader()
            self.form_ready = True
            
        def Show(self) -> None:
            pass

        def Close(self) -> None        :
            pass

class VSpinWithLoader(ABCToolDriver):
    def __init__(self, profile: str) -> None:
        self.profile: str = profile
        self.live: bool = False
        self.client: AxCentrifugeLoader
        self.form: VSpinForm 
        self.instantiate()

    def instantiate(self) -> None:
        """Create form using simpler synchronous approach"""
        pythoncom.CoInitialize()
        
        # Enable Windows XP visual styles
        WinForms.Application.EnableVisualStyles()
        WinForms.Application.SetCompatibleTextRenderingDefault(False)
        self.form = VSpinForm()
        self.form.Show()
        time.sleep(0.5)
        self.client = self.form.Loader
        self.client.CreateControl()
        self.client.Blocking = True
        logging.info("Loader component instantiated successfully")
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
    
    def park(self) -> None:
        self.schedule_threaded_command("park", {})


    def load_plate(self, 
                    bucket_number: int, 
                    gripper_offset: float,
                    plate_height: float, 
                    speed: str, 
                    options: int
                    ) -> None:
        """Load plate"""
        speed_enum = LoadSpeed[speed.upper()]
        
        args = {
            "bucket_number": bucket_number,
            "gripper_offset": gripper_offset,
            "plate_height": plate_height,
            "speed": speed_enum.value,
            "options": options
        }
        self.schedule_threaded_command("load_plate", args)

    def unload_plate(self, bucket_number: int, gripper_offset: float, plate_height: float, speed: str, options: int) -> None:
        """Unload plate"""
        
        speed_enum = LoadSpeed[speed.upper()]

        args = {
            "bucket_number": bucket_number,
            "gripper_offset": gripper_offset,
            "plate_height": plate_height,
            "speed": speed_enum.value,
            "options": options
        }
        self.schedule_threaded_command("unload_plate", args)

    def spin(self, 
                   time: int,
                   velocity_percent: float,
                   acceleration_percent: float,
                   decel_percent: float, 
                   timer_mode: int,
                     bucket: int,
                   ) -> None:
        
        #Validate time. 
        if not (1 < time < 86400):
            raise ValueError("Time must be between 1 and 86400 seconds (24 hours).")
        
        #Since we are not loading/unloading a plate, we will use default values for these parameters.
        gripper_offset_load = 7
        gripper_offset_unload = 7
        plate_height_load = 15
        plate_height_unload = 15

        speed = LoadSpeed.MEDIUM.value  # Default speed for loading

        """Spins the centrifuge with the specified parameters."""
        args : dict = {
            "velocity_percent": velocity_percent,
            "acceleration_percent": acceleration_percent,
            "deceleration_percent": decel_percent,
            "timer_mode": timer_mode,
            "time": time,
            "bucket_number_load": 0, # only spin, skipping loader.
            "bucket_number_unload": bucket,
            "gripper_offset_load": gripper_offset_load,
            "gripper_offset_unload": gripper_offset_unload,
            "plate_height_load": plate_height_load,
            "plate_height_unload": plate_height_unload,
            "speed_load": speed,
            "speed_unload": speed,
            "load_options": 0, # no options
            "unload_options": 0 # no options
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
            elif command == "load_plate":
                response = self.client.LoadPlate(
                    arguments["bucket_number"],
                    arguments["gripper_offset"],
                    arguments["plate_height"],
                    arguments["speed"],
                    arguments["options"]
                )
            elif command == "unload_plate":
                response = self.client.UnloadPlate(
                    arguments["bucket_number"],
                    arguments["gripper_offset"],
                    arguments["plate_height"],
                    arguments["speed"],
                    arguments["options"]
                )
            elif command == "park":
                response = self.client.Park()
            elif command == "spin":
                response = self.client.SpinCycle(
                    arguments["velocity_percent"],
                    arguments["acceleration_percent"],
                    arguments["deceleration_percent"],
                    arguments["timer_mode"],
                    arguments["time"],
                    arguments["bucket_number_load"],
                    arguments["bucket_number_unload"],
                    arguments["gripper_offset_load"],
                    arguments["gripper_offset_unload"],
                    arguments["plate_height_load"],
                    arguments["plate_height_unload"],
                    arguments["speed_load"],
                    arguments["speed_unload"],
                    arguments["load_options"],
                    arguments["unload_options"]
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
        