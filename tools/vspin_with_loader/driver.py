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
                "AxInterop.CentrifugeLoaderLib.dll",
            )
    clr.AddReference(SDK_DLL) 
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
    
    from AxCentrifugeLoaderLib import AxCentrifugeLoader # type: ignore
    import System.Windows.Forms as WinForms  # type: ignore
    import System.Drawing as Drawing  # type: ignore

    class VSpinForm(WinForms.Form):
        def __init__(self):
            super().__init__()
            self.Loader = None
            self.form_ready = False
            self.setup_form()
            
        def setup_form(self):
            """Setup the form like the C# designer code"""
            # Set form properties
            self.AutoScaleDimensions = Drawing.SizeF(6.0, 13.0)
            self.AutoScaleMode = WinForms.AutoScaleMode.Font
            self.ClientSize = Drawing.Size(284, 261)
            self.Name = "VSpinForm"
            self.Text = "VSpin Loader Host"
            self.WindowState = WinForms.FormWindowState.Minimized
            self.ShowInTaskbar = False
            
            # Create the ActiveX control
            self.create_loader_control()
            
        def create_loader_control(self):
            """Create and configure the ActiveX control like C# designer"""
            try:
                # Create the control (like C# designer)
                self.Loader = AxCentrifugeLoader()
                
                # Configure control properties (like C# designer)
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
        
        def SetReady(self):
            """Manual method to set form as ready"""
            self.form_ready = True
            logging.info("Form marked as ready")

else:
    # Stub for non-Windows
    class AxCentrifugeLoader():
        def __init__(self) -> None:
            pass
        
        def Initialize(self, profile: str) -> int:
            return 0
        
        def ShowDiagsDialog(self, modal: bool, level: int) -> int:
            return 0
            
        def Close(self) -> int:
            return 0
            
        def Home(self) -> int:
            return 0
            
        def CloseDoor(self) -> int:
            return 0
            
        def OpenDoor(self, bucket: int) -> int:
            return 0
            
        def LoadPlate(self, bucket: int, offset: float, height: float, speed: int, options: int) -> int:
            return 0
            
        def UnloadPlate(self, bucket: int, offset: float, height: float, speed: int, options: int) -> int:
            return 0
            
        def Park(self) -> int:
            return 0
            
        def SpinCycle(self, *args) -> int:
            return 0
            
        def StopSpinCycle(self, bucket: int) -> int:
            return 0
            
        def GetLastError(self) -> str:
            return ""
            
        @property
        def Blocking(self) -> bool:
            return False
        
        @Blocking.setter 
        def Blocking(self, value: bool) -> None:
            pass
        
    class VSpinForm:
        def __init__(self) -> None:
            self.Loader = AxCentrifugeLoader()
            self.form_ready = True
            
        def Show(self):
            pass
            
        def SetReady(self):
            pass
            
        def Close(self):
            pass

class VSpinWithLoader(ABCToolDriver):
    def __init__(self, profile: str) -> None:
        self.profile: str = profile
        self.live: bool = False
        self.client: AxCentrifugeLoader = None
        self.form: VSpinForm = None
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


    def load_plate(self, bucket_number: int, gripper_offset: float, plate_height: float, speed: int, options: int) -> None:
        """Load plate"""
        args = {
            "bucket_number": bucket_number,
            "gripper_offset": gripper_offset,
            "plate_height": plate_height,
            "speed": speed,
            "options": options
        }
        self.schedule_threaded_command("load_plate", args)

    def unload_plate(self, bucket_number: int, gripper_offset: float, plate_height: float, speed: int, options: int) -> None:
        """Unload plate"""
        args = {
            "bucket_number": bucket_number,
            "gripper_offset": gripper_offset,
            "plate_height": plate_height,
            "speed": speed,
            "options": options
        }
        self.schedule_threaded_command("unload_plate", args)

    def spin_cycle(self, 
                   vel_percent: float, 
                   accel_percent: float, 
                   decel_percent: float, 
                   timer_mode: int,
                   time: int, 
                   bucket_num_load: int, 
                   bucket_num_unload: int,
                   gripper_offset_load: float, 
                   gripper_offset_unload: float, 
                   plate_height_load: float, 
                   plate_height_unload: float, 
                   speed_load: int, 
                   speed_unload: int, 
                   load_options: int, 
                   unload_options: int) -> None:
        """Spins the centrifuge with the specified parameters."""
        args : dict = {
            "velocity_percent": vel_percent,
            "acceleration_percent": accel_percent,
            "deceleration_percent": decel_percent,
            "timer_mode": timer_mode,
            "time": time,
            "bucket_number_load": bucket_num_load,
            "bucket_number_unload": bucket_num_unload,
            "gripper_offset_load": gripper_offset_load,
            "gripper_offset_unload": gripper_offset_unload,
            "plate_height_load": plate_height_load,
            "plate_height_unload": plate_height_unload,
            "speed_load": speed_load,
            "speed_unload": speed_unload,
            "load_options": load_options,
            "unload_options": unload_options
        }
        logging.info(f"Starting spin cycle - velocity: {vel_percent}%, time: {time}s, bucket: {bucket_num_load}")
        self.schedule_threaded_command("spin_cycle", args)

    def stop_spin_cycle(self, bucket_num: int) -> None:
        """Stops the current spin cycle."""
        logging.info("Stopping current spin cycle")
        self.schedule_threaded_command("stop_spin_cycle", {"bucket_number": bucket_num})

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
            elif command == "spin_cycle":
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
        
    def __del__(self):
        """Ensure proper cleanup"""
        try:
            self.close()
        except:
            pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        driver = VSpinWithLoader("vspin")
        logging.info("Testing initialization...")
        driver.initialize()
        
        driver.close_door()
        
        
        logging.info("Teting spin cycle...")
        driver.spin_cycle(
            vel_percent=50.0,
            accel_percent=80.0,
            decel_percent=80.0,
            timer_mode=1,
            time=10,
            bucket_num_load=0,
            bucket_num_unload=1,
            gripper_offset_load=5.0,
            gripper_offset_unload=5.0,
            plate_height_load=10.0,
            plate_height_unload=10.0,
            speed_load=2,
            speed_unload=2,
            load_options=0,
            unload_options=0
        )
        
        logging.info("Testing diagnostics...")
        driver.show_diagnostics()
        
        logging.info("Test completed successfully")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        import traceback
        traceback.print_exc()