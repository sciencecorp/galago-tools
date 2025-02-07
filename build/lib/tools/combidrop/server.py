import logging
import os

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.multidrop_pb2 import  Config

class MultidropServer(ToolServer):
    toolType = "multidrop"
    #driver: HiGCentrifugeDriver
    config: Config

    def __init__(self) -> None:
        super().__init__()
    
    def _configure(self, request:Config) -> None:
        logging.info("Initializing combidrop")
        self.config = request


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    serve(MultidropServer(), os.environ.get("PORT", "4600"))
