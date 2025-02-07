
import os
import logging 
from tools.base_server import ABCToolDriver
import subprocess 
import time 

if os.name == "nt":
    import clr  # type: ignore

    SDK_NAME = "HiGIntegration.dll"
    common_paths = ["C:\\HiG\\", "C:\\Program Files (x86)\\BioNex\\HiG\\"]
    for path in common_paths:
        full_path :str = os.path.join(path,SDK_NAME)
        if os.path.exists(full_path):
            clr.AddReference(full_path) 
            from BioNex import HiGIntegration # type: ignore
            break

else:
    class HiGIntegration: #type: ignore
        def __init__(self, can_port:int)-> None:
            self.can_port: int = can_port
        
        def Initialize(self, name:str, can_port:str, blocking:bool) -> None:
            raise NotImplementedError(
                "HiGInterface is not supported on non-Windows platforms"
            )
        def Home(self) -> None:
            raise NotImplementedError(
                "HiGInterface is not supported on non-Windows platforms"
            )
        def Close(self) -> None:
            raise NotImplementedError(
                "HiGInterface is not supported on non-Windows platforms"
            )
        def ShowDiagnostics(self) -> None:
            raise NotImplementedError(
                "HiGInterface is not supported on non-Windows platforms"
            )
        def OpenShield(self, bucket:int) -> None:
            raise NotImplementedError(
                "HiGInterface is not supported on non-Windows platforms"
            )
        def CloseShield(self) -> None:
            raise NotImplementedError(
                "HiGInterface is not supported on non-Windows platforms"
            )
        def Spin(self,speed_g:int, accel_percent:int,  decel_percent:int, time_seconds:int) -> None:
            raise NotImplementedError(
                "HiGInterface is not supported on non-Windows platforms"
            )
        def AbortSpin(self) -> None:
            raise NotImplementedError(
                "HiGInterface is not supported on non-Windows platforms"
            )
        def HomeShield(self) -> None:
            raise NotImplementedError(
                "HiGInterface is not supported on non-Windows platforms"
            )
        def Dispose(self) -> None:
             raise NotImplementedError(
                "HiGInterface is not supported on non-Windows platforms"
            )           

class HiGCentrifugeDriver(ABCToolDriver):

    def __init__(self , can_port:int) -> None:
        self.can_port: int = can_port
        self.live : bool  = False
        self.client : HiGIntegration
        self.initialize()

    def initialize(self) -> None:
        try:
            p = subprocess.Popen('C:\Program Files (x86)\BioNex\HiG\CanDongleServerProcess.exe', stdout=subprocess.PIPE,shell=True)
            p.poll()
            time.sleep(0.5)
            self.client = HiGIntegration.HiG() #ignore
            self.client.Blocking = True #ignore
            self.client.Initialize("HiG1", str(self.can_port),False) #ignore
            self.live = True 

        except RuntimeError:
            logging.debug("Failed to initialize HiG") 

    def home(self)-> None:
        self.client.Home()

    def spin(self, speed_g:int, accel_percent:int,  decel_percent:int, time_seconds:int)-> None:
        self.client.Spin(speed_g, accel_percent, decel_percent, time_seconds)
    
    def close_shield(self)-> None:
        self.client.CloseShield()
    
    def open_shield(self, bucket:int) -> None:
        self.client.OpenShield(bucket)
    
    def close(self) -> None:
        self.live = False
        self.client.Close()
    
    def show_diagnostics(self) -> None:
        self.client.ShowDiagnostics() 

    def abort_spin(self) -> None:
        return
    