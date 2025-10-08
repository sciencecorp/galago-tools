import logging
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.bioshake_pb2 import Command, Config

from .driver import BioshakeDriver
import argparse 

class BioShakeServer(ToolServer):
    toolType = "bioshake"

    def __init__(self) -> None:
        super().__init__()
        self.driver: BioshakeDriver

    def _configure(self, config: Config) -> None:
        self.config = config
        if self.driver:
            logging.info("Bioshake driver already exists, reconfiguring...")
            self.driver.disconnect()
        self.driver = BioshakeDriver(port=self.config.com_port)
        self.driver.connect()

    def Grip(self, params: Command.Grip) -> None:
        if not self.driver:
            raise Exception("Bioshake driver not connected")
        self.driver.set_elm_lock_pos()

    def Ungrip(self, params: Command.Ungrip) -> None:
        if not self.driver:
            raise Exception("Bioshake driver not connected")
        self.driver.set_elm_unlock_pos()

    def Home(self, params: Command.Home) -> None:
        if not self.driver:
            raise Exception("Bioshake driver not connected")
        self.driver.home()

    def StartShake(self, params: Command.StartShake) -> None:

        if params.duration > 0:
            self.driver.shake_on_with_runtime(
                seconds=params.duration,
                speed=params.speed,
                acceleration=params.acceleration,
            )
        else:
            self.driver.start_shake(
                speed=params.speed,
                acceleration=params.acceleration,
            )

    def StopShake(self, params: Command.StopShake) -> None:
        self.driver.stop_shake()

    def WaitForShakeToFinish(self, params: Command.WaitForShakeToFinish) -> None:
        self.driver.wait_for_shake(timeout=params.timeout)

    def Reset(self, params: Command.Reset) -> None:
        if not self.driver:
            raise Exception("Bioshake driver not connected")
        self.driver.reset()

    def TemperatureOn(self, params: Command.TemperatureOn) -> None:
        self.driver.temp_on()

    def TemperatureOff(self, params: Command.TemperatureOff) -> None:
        self.driver.temp_off()

    def SetTemperature(self, params: Command.SetTemperature) -> None:
        self.driver.set_tmp(params.temperature)
    
    def EstimateGrip(self, params: Command.Grip) -> int:
        return 4

    def EstimateUngrip(self, params: Command.Ungrip) -> int:
        return 4

    def EstimateHome(self, params: Command.Home) -> int:
        return 10

    def EstimateStartShake(self, params: Command.StartShake) -> int:
        return params.duration

    def EstimateStopShake(self, params: Command.StopShake) -> int:
        return 10

    def EstimateReset(self, params: Command.Reset) -> int:
        return 2

    def EstimateWaitForShakeToFinish(self, params: Command.WaitForShakeToFinish) -> int:
        return 5


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
        raise RuntimeWarning("Port must be provided...")
    serve(BioShakeServer(), str(args.port))
