import logging
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.benchcel_pb2 import Command, Config
from .driver import BenchCelDriver
import argparse 

class BenchCelServer(ToolServer):
    toolType = "benchcel"

    def __init__(self) -> None:
        super().__init__()
        self.driver: BenchCelDriver

    def _configure(self, request: Config) -> None:
        logging.info("Initializing BenchCel...")
        self.config = request
        self.driver = BenchCelDriver(request.profile)
    
    def PickAndPlace(self, params: Command.PickAndPlace) -> None:
        logging.info(f"Pick and place from {params.pick_from} to {params.place_to}")
        self.driver.pick_and_place(
            params.pick_from,
            params.place_to,
            params.lidded,
            params.retraction_code
        )
    
    def Delid(self, params: Command.Delid) -> None:
        logging.info(f"Delidding from {params.delid_from} to {params.delid_to}")
        self.driver.delid(
            params.delid_from,
            params.delid_to,
            params.retraction_code
        )
    
    def Relid(self, params: Command.Relid) -> None:
        logging.info(f"Relidding from {params.relid_from} to {params.relid_to}")
        self.driver.relid(
            params.relid_from,
            params.relid_to,
            params.retraction_code
        )
    
    def LoadStack(self, params: Command.LoadStack) -> None:
        logging.info(f"Loading stack {params.stack}")
        self.driver.load_stack(params.stack)
    
    def ReleaseStack(self, params: Command.ReleaseStack) -> None:
        logging.info(f"Releasing stack {params.stack}")
        self.driver.release_stack(params.stack)
    
    def OpenClamp(self, params: Command.OpenClamp) -> None:
        logging.info(f"Opening clamp on stack {params.stack}")
        self.driver.open_clamp(params.stack)
    
    def IsStackLoaded(self, params: Command.IsStackLoaded) -> None:
        logging.info(f"Checking if stack {params.stack} is loaded")
        self.driver.is_stack_loaded(params.stack)
    
    def IsPlatePresent(self, params: Command.IsPlatePresent) -> None:
        logging.info(f"Checking if plate is present on stack {params.stack}")
        self.driver.is_plate_present(params.stack)
    
    def SetLabware(self, params: Command.SetLabware) -> None:
        logging.info(f"Setting labware to {params.labware}")
        self.driver.set_labware(params.labware)
    
    def GetStackCount(self, params: Command.GetStackCount) -> None:
        logging.info("Getting stack count")
        self.driver.get_stack_count()
    
    def GetTeachpointNames(self, params: Command.GetTeachpointNames) -> None:
        logging.info("Getting teachpoint names")
        self.driver.get_teachpoint_names()
    
    def GetLabwareNames(self, params: Command.GetLabwareNames) -> None:
        logging.info("Getting labware names")
        self.driver.get_labware_names()
    
    def ProtocolStart(self, params: Command.ProtocolStart) -> None:
        logging.info("Starting protocol")
        self.driver.protocol_start()
    
    def ProtocolFinish(self, params: Command.ProtocolFinish) -> None:
        logging.info("Finishing protocol")
        self.driver.protocol_finish()
    
    def MoveToHomePosition(self, params: Command.MoveToHomePosition) -> None:
        logging.info("Moving to home position")
        self.driver.move_to_home_position()
    
    def Pause(self, params: Command.Pause) -> None:
        logging.info("Pausing")
        self.driver.pause()
    
    def Unpause(self, params: Command.Unpause) -> None:
        logging.info("Unpausing")
        self.driver.unpause()
    
    def ShowDiagsDialog(self, params: Command.ShowDiagsDialog) -> None:
        logging.info("Showing diagnostics dialog")
        self.driver.show_diagnostics()
    
    def ShowLabwareEditor(self, params: Command.ShowLabwareEditor) -> None:
        logging.info(f"Showing labware editor for {params.labware}")
        self.driver.show_labware_editor(params.modal, params.labware)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
        raise RuntimeWarning("Port must be provided...")
    serve(BenchCelServer(), str(args.port))