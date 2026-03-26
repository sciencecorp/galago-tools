import logging
import math
import time
import typing as t

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.lcus1_relay_pb2 import Command, Config
from tools.grpc_interfaces.tool_base_pb2 import ExecuteCommandReply, INVALID_ARGUMENTS

from .driver import Lcus1RelayDriver
import argparse


class Lcus1RelayServer(ToolServer):
    toolType = "lcus1_relay"
    driver: Lcus1RelayDriver
    config: Config

    def __init__(self) -> None:
        super().__init__()

    def _configure(self, config: Config) -> None:
        self.config = config
        if self.driver:
            self.driver.close()
        self.driver = Lcus1RelayDriver(port=self.config.com_port)
        self.driver.initialize()

    def Switch(self, params: Command.Switch) -> None:
        logging.info(f"Switching relay on port {self.config.com_port} to {params.on}")
        if params.on:
            self.driver.on()
        else:
            self.driver.off()

    def EstimateSwitch(self, params: Command.Switch) -> int:
        return 1

    def TimedSwitch(self, params: Command.TimedSwitch) -> t.Optional[ExecuteCommandReply]:
        if params.duration_seconds <= 0:
            response = ExecuteCommandReply()
            response.response = INVALID_ARGUMENTS
            response.error_message = "duration_seconds must be greater than 0"
            response.return_reply = True
            return response

        logging.info(f"TimedSwitch on port {self.config.com_port} for {params.duration_seconds}s")
        self.driver.on()
        try:
            time.sleep(params.duration_seconds)
        finally:
            self.driver.off()
        return None

    def EstimateTimedSwitch(self, params: Command.TimedSwitch) -> int:
        return math.ceil(params.duration_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    args = parser.parse_args()
    if not args.port:
        raise RuntimeWarning("Port must be provided...")
    serve(Lcus1RelayServer(), str(args.port))
