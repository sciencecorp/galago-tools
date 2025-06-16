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
        self.driver.initialize()
    
    def Home(self, params: Command.Home) -> None:
        self.driver.home()
    
    def CloseDoor(self, params: Command.CloseDoor) -> None:
        self.driver.close_door()
    
    def OpenDoor(self, params: Command.OpenDoor) -> None:
        self.driver.open_door(params.bucket)
    
    def LoadPlate(self, params: Command.LoadPlate) -> None:
        self.driver.load_plate(
            params.bucket,
            params.gripper_offset,
            params.plate_height,
            params.speed,
            params.options
        )
    
    def UnloadPlate(self, params: Command.UnloadPlate) -> None:
        return self.driver.unload_plate(
            params.bucket,
            params.gripper_offset,
            params.plate_height,
            params.speed,
            params.options
        )
    
    def Park(self, params: Command.Park) -> None:
        self.driver.park()
    
    def Spin(self, params: Command.Spin) -> None:
        logging.info(f"Starting spin cycle with parameters: {params}")
        return self.driver.spin(
            params.time,
            params.velocity_percent,
            params.acceleration_percent,
            params.deceleration_percent,
            params.timer_mode,
            params.bucket,
        )
    
    def StopSpin(self, params: Command.StopSpin) -> None:
        return self.driver.stop_spin(params.bucket)

    def ShowDiagsDialog(self, params: Command.ShowDiagsDialog) -> None:
        return self.driver.show_diagnostics()
    
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
    
    def EstimateSpin(self, params: Command.Spin) -> int:
        return 1 
    
    def EstimateStopSpin(self, params: Command.StopSpin) -> int:
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