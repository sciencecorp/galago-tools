import logging
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.plateloc_pb2 import Command, Config
from .driver import PlateLocDriver
import argparse 

class PlateLocServer(ToolServer):
     toolType = "plateloc"

     def __init__(self) -> None:
          super().__init__()
          self.driver : PlateLocDriver

     def _configure(self, request:Config) -> None:
          logging.info("Initializing Plateloc...")
          self.config = request
          self.driver = PlateLocDriver(request.profile)
     
     def ShowDiagsDialog(self, params:Command.ShowDiagsDialog) -> None:
          self.driver.show_diagnostics()
     
     def SetTemperature(self, params:Command.SetTemperature) -> None:
          logging.info(f"Setting temperature to {params.temperature}")
          self.driver.set_temperature(params.temperature)
     
     def SetSealTime(self, params:Command.SetSealTime) -> None:
          logging.info(f"Setting time to {params.time}")
          self.driver.set_seal_time(params.time)
     
     def GetActualTemperature(self, params:Command.GetActualTemperature) -> None:
          self.driver.get_actual_temperature()
     
     def StageIn(self, params:Command.StageIn) -> None:
          self.driver.stage_in()
     
     def StageOut(self, params:Command.StageOut) -> None:
          self.driver.stage_out()
     
     def Seal(self, params:Command.Seal) -> None:
          self.driver.seal()
          self.driver.stage_out()
     

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    serve(PlateLocServer(), str(args.port))
