import logging
import os
import argparse 
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.bravo_pb2 import Command, Config
from .driver_v2 import BravoDriver

class BravoServer(ToolServer):
    toolType = "bravo"
    #driver: HiGCentrifugeDriver
    config: Config

    def __init__(self) -> None:
        super().__init__()
        self.driver: BravoDriver
    
    def _configure(self, request:Config) -> None:
        logging.info("Initializing Bravo")
        self.config = request
        self.driver = BravoDriver()
        self.driver.login()
    
    def RunProtocol(self, params:Command.RunProtocol) -> None:
        self.driver.run_protocol(params.protocol_file)
    
    def RunRunset(self, params:Command.RunRunset) -> None:
        self.driver.run_runset(params.runset_file)
   
    def EstimateRunProtocol(self, params:Command.RunProtocol) -> int:
        return 1
    
    def EstimateRunRunset(self, params:Command.RunRunset) -> int:
        return 1
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    else:
        serve(BravoServer(),os.environ.get("PORT", str(args.port)))
