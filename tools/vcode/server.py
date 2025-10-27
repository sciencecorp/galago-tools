import logging

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.vcode_pb2 import Command, Config
from .driver import VCodeDriver
import argparse 

class VCodeServer(ToolServer):
    toolType = "vcode"

    def __init__(self) -> None:
        super().__init__()
        self.driver : VCodeDriver

    def _configure(self, request:Config) -> None:
        logging.info("Initializing VCode...")
        self.config = request
        self.driver = VCodeDriver(request.profile)
        return self.driver.initialize()
    
    def Home(self, params:Command.Home) -> None:
        return self.driver.home_stage()
    
    def PrintAndApply(self, params:Command.PrintAndApply) -> None:
        return self.driver.print_and_apply_by_name(
            params.format_name,
            params.side, 
            params.drop_stage, 
            params.field_0,
            params.field_1,
            params.field_2,
            params.field_3,
            params.field_4,
            params.field_5
        )
    
    def Print(self, params:Command.Print) -> None:
        return self.driver.print_label(
            params.format_name,
            params.field_0,
            params.field_1,
            params.field_2,
            params.field_3,
            params.field_4,
            params.field_5
        )
    
    def Rotate180(self, params:Command.Rotate180) -> None:
        return self.driver.rotate180()
    
    def RotateStage(self, params:Command.RotateStage) -> None:
        return self.driver.rotate_stage(params.angle)
    
    def ShowDiagsDialog(self, params:Command.ShowDiagsDialog) -> None:
        return self.driver.show_diagnostics()

    def DropStage(self, params:Command.DropStage) -> None:
        return self.driver.drop_stage(params.drop_stage)
    
    def EstimatePrintAndApply(self, params: Command.PrintAndApply) -> int:
        return 1
    
    def EstimateHome(self, params: Command.Home) -> int:
        return 1
    
    def EstimatePrint(self, params: Command.Print) -> int:
        return 1
    
    def EstimateRotate180(self, params: Command.Rotate180) -> int:
        return 1
    
    def EstimateDropStage(self, params: Command.DropStage) -> int:
        return 1
    
    def EstimateShowDiagsDialog(self, params: Command.ShowDiagsDialog) -> int:
        return 1
    
    def EstimateRotateStage(self, params: Command.RotateStage) -> int:
        return 1

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    serve(VCodeServer(), str(args.port))
