import logging

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.hamilton_pb2 import Command, Config
from .driver import HamiltonDriver 

import argparse

class HamiltonServer(ToolServer):
    toolType = "hamilton"

    def __init__(self) -> None:
        super().__init__()
        self.driver : HamiltonDriver

    def _configure(self, request:Config) -> None:
        logging.info("Initializing Hamilton STAR")
        self.driver = HamiltonDriver()

    def RunProtocol(self, params:Command.RunProtocol) -> None:
        self.driver.run_protocol(params.protocol)

    def LoadProtocol(self, params:Command.LoadProtocol) -> None:
        self.driver.load_protocol(params.protocol)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    serve(HamiltonServer(), str(args.port))
