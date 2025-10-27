import logging 
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.hig_centrifuge_pb2 import Command, Config
from .driver import HiGCentrifugeDriver
import argparse 

class HiGCentrifugeServer(ToolServer):
    toolType = "hig_centrifuge"
    driver: HiGCentrifugeDriver
    config: Config

    def __init__(self) -> None:
        super().__init__()
        self.driver: HiGCentrifugeDriver
    
    def _configure(self, request:Config) -> None:
        logging.info("Initializing HiG")
        self.config = request
        self.driver = HiGCentrifugeDriver(can_port=0)
        self.driver.initialize()
        self.driver.home()
        
    def Home(self, params: Command.Home) -> None:
        self.driver.home()
    
    def Spin(self, params: Command.Spin) -> None:
        self.driver.spin(params.speed, params.acceleration, params.decceleration, params.duration)
    
    def OpenShield(self, params: Command.OpenShield) -> None:
        self.driver.open_shield(params.bucket_id)
    
    def CloseShield(self, params: Command.CloseShield) -> None:
        self.driver.close_shield()
    
    def EstimateHome(self, params: Command.Home) -> int:
        return 1
    def EstimateSpin(self, params: Command.Spin) -> int:
        return 1
    def EstimateOpenShield(self, params: Command.OpenShield) -> int:
        return 1
    def EstimateCloseShield(self, params: Command.CloseShield) -> int:
        return 1

    

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
        raise RuntimeWarning("Port must be provided...")
    serve(HiGCentrifugeServer(), str(args.port))