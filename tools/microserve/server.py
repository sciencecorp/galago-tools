import logging
import os
import time

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.microserve_pb2 import Command, Config

from tools.grpc_interfaces.tool_base_pb2 import ExecuteCommandReply
from tools.grpc_interfaces.tool_base_pb2 import SUCCESS

from .driver import MicroServeDriver

import argparse

class MicroserveServer(ToolServer):
    toolType = "microserve"
    driver: MicroServeDriver
    config: Config

    def __init__(self) -> None:
        super().__init__()

    def _configure(self, config: Config) -> None:
        self.config = config
        if self.driver:
            self.driver.disconnect()
        self.driver = MicroServeDriver(self.config.ip, self.config.port)
        self.driver.connect()
        
    def Load(self, params: Command.Load) -> None:
        self.driver.load(params.stack_id, params.plate_height, params.plate_thickness, params.stack_height)

    def Unload(self, params: Command.Unload) -> None:
        self.driver.unload(params.stack_id, params.plate_height, params.plate_thickness, params.stack_height)

    def Home(self, params: Command.Home) -> None:
        self.driver.home()

    def Retract(self, params:Command.Retract) -> None:
        self.driver.retract()

    def GoTo(self, params:Command.GoTo) -> None:
        self.driver.go_to(params.stack_id)

    def Abort(self, params:Command.Abort) -> None:
        self.driver.abort()

    def SendRawCommand(self, params: Command.SendRawCommand) -> None:
        logging.info(f"Sending raw command {params.command}")
        return self.driver.send_command(params.command)

if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().setLevel(logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    logging.info("Running server")
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    serve(MicroserveServer(), os.environ.get("PORT", str(args.port)))
