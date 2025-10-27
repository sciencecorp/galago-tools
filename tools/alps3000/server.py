import logging

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.alps3000_pb2 import Command, Config
from .driver import ALPS3000Driver
import argparse
import time 

class ALPS3000Server(ToolServer):
    toolType = "alps3000"

    def __init__(self) -> None:
        super().__init__()
        self.driver: ALPS3000Driver

    def _configure(self, request: Config) -> None:
        logging.info("Initializing ALPS 3000...")
        self.config = request
        self.driver = ALPS3000Driver(profile=request.profile, port=request.com_port)
        return self.driver.initialize()

    def GetInstrumentStatus(self, params: Command.GetInstrumentStatus) -> None:
        return self.driver.get_status()

    def SealPlate(self, params: Command.SealPlate) -> None:
        self.driver.seal_plate()
        time.sleep(12)

    def GetError(self, params: Command.GetError) -> None:
        self.driver.get_error()

    def SetTemperature(self, params: Command.SetTemperature) -> None:
        self.driver.set_sealing_temperature(params.temperature)

    def SetSealTime(self, params: Command.SetSealTime) -> None:
        self.driver.set_sealing_time(params.seal_time)

    def GetTemperatureSetpoint(self, params: Command.GetTemperatureSetpoint) -> None:
        self.driver.get_sealing_temperature_setpoint()

    def GetSealingTime(self, params: Command.GetSealingTime) -> None:
        self.driver.get_sealing_time()

    def GetTemperatureActual(self, params: Command.GetTemperatureActual) -> None:
        self.driver.get_sealing_temperature_actual()

    def EstimateSealPlate(self, params: Command.SealPlate) -> int:
        return 1
    
    def EstimateGetError(self, params: Command.GetError) -> int:
        return 1
    
    def EstimateSetTemperature(self, params: Command.SetTemperature) -> int:
        return 1
    


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
        raise RuntimeWarning("Port must be provided...")
    serve(ALPS3000Server(), str(args.port))
