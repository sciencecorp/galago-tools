import logging
import argparse
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.bravo_pb2 import  Config
from .driver import BravoDriver


class BravoServer(ToolServer):
    toolType = "bravo"
    config : Config
    
    def __init__(self) -> None:
        super().__init__()
        self.driver : BravoDriver 
        
    def _configure(self, config: Config) -> None:
        self.config = config

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True, help='Port number for gRPC server')
    args = parser.parse_args()
    
    logging.info("Starting Bravo gRPC server...")
    serve(BravoServer(), str(args.port))