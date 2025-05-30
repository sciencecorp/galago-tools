import logging
import os
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.vspin_with_loader_pb2 import Command, Config
from .driver import VSpinWithLoader
import argparse 

class VSpinWithLoaderServer(ToolServer):
    toolType = "vspin_with_loader"
    
    def __init__(self) -> None:
        super().__init__()
        self.driver: VSpinWithLoader
    
    def _configure(self, request: Config) -> None:
        logging.info("Initializing VSpin and Loader...")
        self.config = request
        self.driver = VSpinWithLoader(request.profile)
        return self.driver.initialize()
    
    def Initialize(self, params: Command.Initialize) -> None:
        return self.driver.initialize()
    
    def Close(self, params: Command.Close) -> None:
        return self.driver.close()
    
    def Home(self, params: Command.Home) -> None:
        return self.driver.home()
    
    def CloseDoor(self, params: Command.CloseDoor) -> None:
        return self.driver.close_door()
    
    def OpenDoor(self, params: Command.OpenDoor) -> None:
        return self.driver.open_door(params.bucket_number)
    
    def LoadPlate(self, params: Command.LoadPlate) -> None:
        return self.driver.load_plate(
            params.bucket_number,
            params.gripper_offset,
            params.plate_height,
            params.speed,
            params.options
        )
    
    def UnloadPlate(self, params: Command.UnloadPlate) -> None:
        return self.driver.unload_plate(
            params.bucket_number,
            params.gripper_offset,
            params.plate_height,
            params.speed,
            params.options
        )
    
    def Park(self, params: Command.Park) -> None:
        return self.driver.park()
    
    def SpinCycle(self, params: Command.SpinCycle) -> None:
        return self.driver.spin_cycle(
            params.velocity_percent,
            params.acceleration_percent,
            params.deceleration_percent,
            params.timer_mode,
            params.time,
            params.bucket_number_load,
            params.gripper_offset_load,
            params.gripper_offset_unload,
            params.plate_height_load,
            params.plate_height_unload,
            params.speed_load,
            params.speed_unload,
            params.load_options,
            params.unload_options
        )
    
    def StopSpinCycle(self, params: Command.StopSpinCycle) -> None:
        return self.driver.stop_spin_cycle(params.bucket_number)
    
    def ShowDiagsDialog(self, params: Command.ShowDiagsDialog) -> None:
        return self.driver.show_diagnostics(params.modal, params.level)
    
    def EstimateInitialize(self, params: Command.Initialize) -> int:
        return 2  
    
    def EstimateClose(self, params: Command.Close) -> int:
        return 2
    
    def EstimateHome(self, params: Command.Home) -> int:
        return 2
    
    def EstimateCloseDoor(self, params: Command.CloseDoor) -> int:
        return 3
    
    def EstimateOpenDoor(self, params: Command.OpenDoor) -> int:
        return 3
    
    def EstimateLoadPlate(self, params: Command.LoadPlate) -> int:
        return 1
    
    def EstimateUnloadPlate(self, params: Command.UnloadPlate) -> int:
        return 1
    
    def EstimatePark(self, params: Command.Park) -> int:
        return 1
    
    def EstimateSpinCycle(self, params: Command.SpinCycle) -> int:
        base_time = params.time if params.time > 0 else 1 
        accel_decel_time = 20  # Estimated time for acceleration and deceleration
        load_unload_time = 16  # Time for loading and unloading operations
        return base_time + accel_decel_time + load_unload_time
    
    def EstimateStopSpinCycle(self, params: Command.StopSpinCycle) -> int:
        return 1 
    
    def EstimateShowDiagsDialog(self, params: Command.ShowDiagsDialog) -> int:
        return 1  


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
        raise RuntimeWarning("Port must be provided...")
    serve(VSpinWithLoaderServer(), os.environ.get("PORT", str(args.port)))