import logging
import time

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.liconic_pb2 import Command, Config

from tools.grpc_interfaces.tool_base_pb2 import ExecuteCommandReply
from tools.grpc_interfaces.tool_base_pb2 import SUCCESS

from .driver import LiconicStxDriver

import argparse

class LiconicServer(ToolServer):
    toolType = "liconic"
    driver: LiconicStxDriver
    config: Config

    def __init__(self) -> None:
        super().__init__()

    def _configure(self, config: Config) -> None:
        self.config = config
        if self.driver:
            self.driver.close()
        self.driver = LiconicStxDriver(self.config.com_port)
        self.driver.start_monitor()
        
    def FetchPlate(self, params: Command.FetchPlate) -> None:
        response = ExecuteCommandReply()
        response.return_reply = True
        response.response = SUCCESS
        #try:            
        if params.cassette < 1 or params.level < 1:
            raise ValueError(
                f"Cassette ({params.cassette}) and level ({params.level}) must be positive integers"
            )
        self.driver.unload_plate(params.cassette, params.level)
        time.sleep(6)

    def StorePlate(self, params: Command.StorePlate) -> None:
        response = ExecuteCommandReply()
        response.return_reply = True
        response.response = SUCCESS
        #try:            
        if params.cassette < 1 or params.level < 1:
            raise ValueError(
                f"Cassette ({params.cassette}) and level ({params.level}) must be positive integers"
            )
        self.driver.load_plate(params.cassette, params.level)
        time.sleep(6)


    def Reset(self, params: Command.Reset) -> None:
        self.driver.reset()

    def EstimateFetchPlate(self, params: Command.FetchPlate) -> int:
        return 1

    def EstimateStorePlate(self, params: Command.StorePlate) -> int:
        return 1

    def EstimateReset(self, params: Command.Reset) -> int:
        return 1

    def SendRawCommand(self, params: Command.SendRawCommand) -> None:
        logging.info(f"Sending raw command {params.cmd}")
        return self.driver.raw(params.cmd)

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    logging.info("Running server")
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    serve(LiconicServer(), str(args.port))