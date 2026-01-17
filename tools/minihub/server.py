import logging
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.minihub_pb2 import Command, Config
from .driver import MiniHubDriver
import argparse 

class MiniHubServer(ToolServer):
     toolType = "minihub"

     def __init__(self) -> None:
          super().__init__()
          self.driver: MiniHubDriver

     def _configure(self, request: Config) -> None:
          logging.info("Initializing MiniHub...")
          self.config = request
          self.driver = MiniHubDriver(request.profile)
     
     def ShowDiagsDialog(self, params: Command.ShowDiagsDialog) -> None:
          self.driver.show_diagnostics()
     
     def Abort(self, params: Command.Abort) -> None:
          logging.info("Aborting current task")
          self.driver.abort()
     
     def Close(self, params: Command.Close) -> None:
          logging.info("Closing MiniHub")
          self.driver.close()
     
     def DisableMotor(self, params: Command.DisableMotor) -> None:
          logging.info("Disabling motor")
          self.driver.disable_motor()
     
     def EnableMotor(self, params: Command.EnableMotor) -> None:
          logging.info("Enabling motor")
          self.driver.enable_motor()
     
     def Jog(self, params: Command.Jog) -> None:
          logging.info(f"Jogging {params.degree} degrees, clockwise={params.clockwise}")
          self.driver.jog(params.degree, params.clockwise)
     
     def RotateToCassette(self, params: Command.RotateToCassette) -> None:
          logging.info(f"Rotating to cassette {params.cassette_index}")
          self.driver.rotate_to_cassette(params.cassette_index)
     
     def RotateToDegree(self, params: Command.RotateToDegree) -> None:
          logging.info(f"Rotating to {params.degree} degrees")
          self.driver.rotate_to_degree(params.degree)
     
     def RotateToHomePosition(self, params: Command.RotateToHomePosition) -> None:
          logging.info("Rotating to home position")
          self.driver.rotate_to_home_position()
     
     def SetSpeed(self, params: Command.SetSpeed) -> None:
          logging.info(f"Setting speed to {params.speed}")
          self.driver.set_speed(params.speed)
     
     def TeachHome(self, params: Command.TeachHome) -> None:
          logging.info("Teaching home position")
          self.driver.teach_home()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    serve(MiniHubServer(), str(args.port))