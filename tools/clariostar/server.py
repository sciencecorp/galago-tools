import argparse
import logging

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.clariostar_pb2 import Command, Config
from tools.grpc_interfaces.tool_base_pb2 import ExecuteCommandReply, SUCCESS

from .driver import CLARIOstarDriver


class ClariostarServer(ToolServer):
    toolType = "clariostar"

    def __init__(self) -> None:
        super().__init__()
        self.driver: CLARIOstarDriver

    def _configure(self, config: Config) -> None:
        self.config = config
        if self.driver:
            self.driver.close()
        if (
            not config.protocol_dir
            or not config.data_dir
            or not config.device_name
            or not config.output_dir
        ):
            raise RuntimeError(
                "Protocol directory, experiment directory, and reader type must be specified in the configuration."
            )
        self.driver = CLARIOstarDriver(
            protocol_dir=config.protocol_dir,
            data_dir=config.data_dir,
            output_dir=config.output_dir,
            device_name=config.device_name,
        )
        self.driver.open_connection()

    def OpenCarrier(self, params: Command.OpenCarrier) -> None:
        self.driver.plate_out()

    def CloseCarrier(self, params: Command.CloseCarrier) -> None:
        self.driver.plate_in()

    def StartRead(self, params: Command.StartRead) -> ExecuteCommandReply:
        data = self.driver.run_protocol(
            protocol_name=params.protocol_name,
            plate_id=params.plate_id,
            assay_id=params.assay_id,
            timepoint=params.timepoint,
        )
        response = ExecuteCommandReply(response=SUCCESS, return_reply=True)
        if data:
            response.meta_data.update({"data": data})
        return response

    def SetTemperature(self, params: Command.SetTemperature) -> None:
        self.driver.set_temperature(temperature=params.temperature)

    def EstimateOpenCarrier(self, params: Command.OpenCarrier) -> int:
        return 2

    def EstimateCloseCarrier(self, params: Command.CloseCarrier) -> int:
        return 2

    def EstimateStartRead(self, params: Command.StartRead) -> int:
        return 5

    def EstimateSetTemperature(self, params: Command.SetTemperature) -> int:
        return 600


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    args = parser.parse_args()
    if not args.port:
        raise RuntimeWarning("Port must be provided...")
    serve(ClariostarServer(), str(args.port))
