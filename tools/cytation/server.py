import logging

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.cytation_pb2 import Command, Config

from .driver import CytationDriver
import argparse 

class CytationServer(ToolServer):
    toolType = "cytation"

    def __init__(self) -> None:
        super().__init__()
        self.driver: CytationDriver

    def _configure(self, config: Config) -> None:
        self.config = config
        if self.driver:
            self.driver.close()
        if not config.protocol_dir or not config.experiment_dir or not config.reader_type:
            raise RuntimeError("Protocol directory, experiment directory, and reader type must be specified in the configuration.")
        self.driver = CytationDriver(
            protocol_dir=config.protocol_dir,
            experiment_dir=config.experiment_dir,
            reader_type=config.reader_type,
        )
        self.driver.verify_reader_communication()

    def OpenCarrier(self, params: Command.OpenCarrier) -> None:
        self.driver.open_carrier()

    def CloseCarrier(self, params: Command.CloseCarrier) -> None:
        self.driver.close_carrier()

    def StartRead(self, params: Command.StartRead) -> None:
        self.driver.start_read(
            protocol_file=params.protocol_file,
            experiment_name=params.experiment_name,
            well_addresses=[addy for addy in params.well_addresses],
        )

    def EstimateOpenCarrier(self, params: Command.OpenCarrier) -> int:
        return 2

    def EstimateCloseCarrier(self, params: Command.CloseCarrier) -> int:
        return 2

    def EstimateStartRead(self, params: Command.StartRead) -> int:
        return 5


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    serve(CytationServer(), str(args.port))
