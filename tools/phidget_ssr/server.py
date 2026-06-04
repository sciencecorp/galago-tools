import argparse
import logging
import math
import time
import typing as t

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.phidget_ssr_pb2 import Command, Config
from tools.grpc_interfaces.tool_base_pb2 import ExecuteCommandReply, INVALID_ARGUMENTS

from .driver import PhidgetSSRDriver

NUM_CHANNELS = 4


class PhidgetSSRServer(ToolServer):
    toolType = "phidget_ssr"
    driver: PhidgetSSRDriver
    config: Config

    def __init__(self) -> None:
        super().__init__()

    def _configure(self, config: Config) -> None:
        self.config = config
        if self.driver:
            self.driver.close()
        self.driver = PhidgetSSRDriver(
            hub_port=config.hub_port,
            serial_number=config.serial_number if config.HasField("serial_number") else None,
            frequency=config.frequency if config.HasField("frequency") else None,
        )
        self.driver.initialize()

    def _invalid(self, message: str) -> ExecuteCommandReply:
        response = ExecuteCommandReply()
        response.response = INVALID_ARGUMENTS
        response.error_message = message
        response.return_reply = True
        return response

    def _validate(self, channel: int, duty_cycle: float) -> t.Optional[ExecuteCommandReply]:
        if not 0 <= channel < NUM_CHANNELS:
            return self._invalid(f"channel must be in 0..{NUM_CHANNELS - 1}, got {channel}")
        if not 0.0 <= duty_cycle <= 1.0:
            return self._invalid(f"duty_cycle must be in 0.0..1.0, got {duty_cycle}")
        return None

    def SetDutyCycle(self, params: Command.SetDutyCycle) -> t.Optional[ExecuteCommandReply]:
        error = self._validate(params.channel, params.duty_cycle)
        if error is not None:
            return error
        logging.info(f"SetDutyCycle channel={params.channel} duty_cycle={params.duty_cycle}")
        self.driver.set_duty_cycle(params.channel, params.duty_cycle)
        return None

    def EstimateSetDutyCycle(self, params: Command.SetDutyCycle) -> int:
        return 1

    def TimedDutyCycle(self, params: Command.TimedDutyCycle) -> t.Optional[ExecuteCommandReply]:
        error = self._validate(params.channel, params.duty_cycle)
        if error is not None:
            return error
        if params.duration_seconds <= 0:
            return self._invalid("duration_seconds must be greater than 0")
        logging.info(
            f"TimedDutyCycle channel={params.channel} duty_cycle={params.duty_cycle} "
            f"for {params.duration_seconds}s"
        )
        self.driver.set_duty_cycle(params.channel, params.duty_cycle)
        try:
            time.sleep(params.duration_seconds)
        finally:
            self.driver.set_duty_cycle(params.channel, 0.0)
        return None

    def EstimateTimedDutyCycle(self, params: Command.TimedDutyCycle) -> int:
        return math.ceil(params.duration_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    args = parser.parse_args()
    if not args.port:
        raise RuntimeWarning("Port must be provided...")
    serve(PhidgetSSRServer(), str(args.port))
