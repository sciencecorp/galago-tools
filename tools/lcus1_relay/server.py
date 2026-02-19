import logging

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.lcus1_relay_pb2 import Command, Config

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


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    args = parser.parse_args()
    if not args.port:
        raise RuntimeWarning("Port must be provided...")
    serve(Lcus1RelayServer(), str(args.port))
