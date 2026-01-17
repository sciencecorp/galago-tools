import logging
import os
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.vspin_pb2 import Command, Config
from .driver import VSpin
import argparse 

class VSpinServer(ToolServer):
    toolType = "vspin"
    
    def __init__(self) -> None:
        super().__init__()
        self.driver: VSpin
    
    def _configure(self, request: Config) -> None:
        logging.info("Initializing VSpin and Loader...")
        self.config = request
        self.driver = VSpin(request.profile)
        self.driver.initialize()
    
    def Home(self, params: Command.Home) -> None:
        self.driver.home()
    
    def CloseDoor(self, params: Command.CloseDoor) -> None:
        self.driver.close_door()
    
    def OpenDoor(self, params: Command.OpenDoor) -> None:
        self.driver.open_door(params.bucket)
    
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
    serve(VSpinServer(), os.environ.get("PORT", str(args.port)))