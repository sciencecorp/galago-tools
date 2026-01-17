import logging
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.vstack_pb2 import Command, Config
from .driver import VStackDriver 
import argparse 

class VStackServer(ToolServer):
     toolType = "vstack"

     def __init__(self) -> None:
          super().__init__()
          self.driver: VStackDriver

     def _configure(self, request: Config) -> None:
          logging.info("Initializing VStack...")
          self.config = request
          self.driver = VStackDriver(request.profile)
     
     def ShowDiagsDialog(self, params: Command.ShowDiagsDialog) -> None:
          self.driver.show_diagnostics()
     
     def Abort(self, params: Command.Abort) -> None:
          logging.info("Aborting current task")
          self.driver.abort()
     
     def Close(self, params: Command.Close) -> None:
          logging.info("Closing VStack")
          self.driver.close()
     
     def Downstack(self, params: Command.Downstack) -> None:
          logging.info("Performing downstack operation")
          self.driver.downstack()
     
     def Home(self, params: Command.Home) -> None:
          logging.info("Homing stage")
          self.driver.home()
     
     def Jog(self, params: Command.Jog) -> None:
          logging.info(f"Jogging stage by {params.increment} mm")
          self.driver.jog(params.increment)
     
     def LoadStack(self, params: Command.LoadStack) -> None:
          logging.info("Loading stack")
          self.driver.load_stack()
     
     def OpenGripper(self, params: Command.OpenGripper) -> None:
          logging.info(f"Setting gripper open={params.open}")
          self.driver.open_gripper(params.open)
     
     def ReleaseStack(self, params: Command.ReleaseStack) -> None:
          logging.info("Releasing stack")
          self.driver.release_stack()
     
     def SetButtonMode(self, params: Command.SetButtonMode) -> None:
          logging.info(f"Setting button mode: run_mode={params.run_mode}")
          self.driver.set_button_mode(params.run_mode, params.reply)
     
     def SetLabware(self, params: Command.SetLabware) -> None:
          logging.info(f"Setting labware to {params.labware}")
          self.driver.set_labware(params.labware, params.plate_dimension_select)
     
     def Upstack(self, params: Command.Upstack) -> None:
          logging.info("Performing upstack operation")
          self.driver.upstack()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    serve(VStackServer(), str(args.port))