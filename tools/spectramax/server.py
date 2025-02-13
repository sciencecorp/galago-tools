import logging

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.spectramax_pb2 import Command, Config
import sys
from .driver import SpectramaxDriver
import argparse

class SpectramaxServer(ToolServer):
    toolType = "spectramax"

    def __init__(self) -> None:
        super().__init__()
        self.driver: SpectramaxDriver

    def _configure(self, config: Config) -> None:
        self.config = config
        if self.driver:
            self.driver.close()
        self.driver = SpectramaxDriver(
            protocol_dir=config.protocol_dir, experiment_dir=config.experiment_dir
        )
        self.driver.start()
        self.driver.verify_reader_communication()

    def OpenDrawer(self, params: Command.OpenDrawer) -> None:
        self.driver.open_drawer()

    def CloseDrawer(self, params: Command.CloseDrawer) -> None:
        self.driver.close_drawer()

    def StartRead(self, params: Command.StartRead) -> None:
        self.driver.start_experiment(
            protocol_file=params.protocol_file, experiment_name=params.experiment_name
        )

    def EstimateOpenDrawer(self, params: Command.OpenDrawer) -> int:
        return 2

    def EstimateCloseDrawer(self, params: Command.CloseDrawer) -> int:
        return 2

    def EstimateStartRead(self, params: Command.StartRead) -> int:
        return 5


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    known, remaining = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + remaining
    
    if not known.port:
        raise RuntimeWarning("Port must be provided...")
    serve(SpectramaxServer(),str(known.port))
