import logging
import time
import typing as t

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.bioshake_pb2 import Command, Config

from .driver import BioshakeDriver
import argparse 

class BioShakeServer(ToolServer):
    toolType = "bioshake"

    def __init__(self) -> None:
        super().__init__()
        self.driver: t.Optional[BioshakeDriver] = None

    def _configure(self, config: Config) -> None:
        self.config = config
        if self.driver:
            logging.info("Bioshake driver already exists, reconfiguring...")
            self.driver.port = self.config.com_port
        else:
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
        self.driver.shake_go_home()

    def StartShake(self, params: Command.StartShake) -> None:
        if not self.driver:
            raise Exception("Bioshake driver not connected")
        self.driver.set_shake_target_speed(rpm=params.speed)
        if params.duration > 0:
            # Note, this is not blocking meaning that command will return
            # And next command will be executed immediately
            # This enables shaking to happen asynchronously which enables
            # stop commands to be issued, but also means that workcell can
            # do other things while shaking is happening
            # However, this also means that when we want to wait for
            # shaking to finish, we need to use WaitForShakeToFinish
            self.driver.shake_on_with_runtime(seconds=params.duration)
        else:
            self.driver.shake_on()

    def StopShake(self, params: Command.StopShake) -> None:
        if not self.driver:
            raise Exception("Bioshake driver not connected")
        self.driver.shake_off()
        time.sleep(4)

    def WaitForShakeToFinish(self, params: Command.WaitForShakeToFinish) -> None:
        """Note, this is a blocking command that waits for shake to finish
        for a maximum of params.timeout seconds. If shake is not finished
        within that time, it will return None. If it is desired for shake to
        end, then a stop shake command will need to be sent. Alternatively,
        the shake will stop once the time originally given to it has elapsed.
        """
        if not self.driver:
            raise Exception("Bioshake driver not connected")
        start_time = time.time()
        while time.time() - start_time < params.timeout:
            remaining_time = self.driver.get_shake_remaining_time()
            shake_state = self.driver.get_shake_state_as_string()
            logging.info(
                f"Current status: {shake_state}... Shake remaining time: {remaining_time}"
            )
            if remaining_time == 0 or shake_state in ["STOP", "ESTOP"]:
                logging.info("Shake finished")
                return None
            else:
                time.sleep(5)
        logging.warning("Timeout reached shake not finished")
        return None

    def Reset(self, params: Command.Reset) -> None:
        if not self.driver:
            raise Exception("Bioshake driver not connected")
        self.driver.reset_device()

    def EstimateGrip(self, params: Command.Grip) -> int:
        return 1

    def EstimateUngrip(self, params: Command.Ungrip) -> int:
        return 1

    def EstimateHome(self, params: Command.Home) -> int:
        return 1

    def EstimateStartShake(self, params: Command.StartShake) -> int:
        return 1

    def EstimateStopShake(self, params: Command.StopShake) -> int:
        return 1

    def EstimateReset(self, params: Command.Reset) -> int:
        return 1

    def EstimateWaitForShakeToFinish(self, params: Command.WaitForShakeToFinish) -> int:
        return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
        raise RuntimeWarning("Port must be provided...")
    serve(BioShakeServer(), str(args.port))
