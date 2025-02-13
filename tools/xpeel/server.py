import logging

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.xpeel_pb2 import Command, Config  # Adjust the import paths according to your actual protobuf files

from tools.grpc_interfaces.tool_base_pb2 import ExecuteCommandReply
from tools.grpc_interfaces.tool_base_pb2 import INVALID_ARGUMENTS, SUCCESS
import sys 
from .driver import XPeelDriver
import argparse 

class XPeelServer(ToolServer):
    toolType = "xpeel"
    driver: XPeelDriver
    config: Config

    def __init__(self) -> None:
        super().__init__()

    def _configure(self, config: Config) -> None:
        self.config = config
        if self.driver:
            self.driver.close()
        self.driver = XPeelDriver(self.config.com_port)

    def Peel(self, params: Command.Peel) -> None:
        response = ExecuteCommandReply()
        response.return_reply = True
        response.response = SUCCESS
        try:
            self.driver.remove_seal()
        except Exception as exc:
            logging.exception("Failed to deseal plate", exc)
            response.response = INVALID_ARGUMENTS

    def CheckStatus(self) -> ExecuteCommandReply:
        response = ExecuteCommandReply()
        response.return_reply = True
        response.response = SUCCESS
        try:
            self.driver.check_status()
        except Exception as exc:
            logging.exception("Failed to check status", exc)
            response.response = INVALID_ARGUMENTS
        return response

    def Reset(self) -> ExecuteCommandReply:
        response = ExecuteCommandReply()
        response.return_reply = True
        response.response = SUCCESS
        try:
            self.driver.reset()
        except Exception as exc:
            logging.exception("Failed to reset device", exc)
            response.response = INVALID_ARGUMENTS
        return response

    def Restart(self) -> ExecuteCommandReply:
        response = ExecuteCommandReply()
        response.return_reply = True
        response.response = SUCCESS
        try:
            self.driver.restart()
        except Exception as exc:
            logging.exception("Failed to restart device", exc)
            response.response = INVALID_ARGUMENTS
        return response

    def GetRemainingTape(self) -> ExecuteCommandReply:
        response = ExecuteCommandReply()
        response.return_reply = True
        response.response = SUCCESS
        try:
            self.driver.check_tape_remaining()
        except Exception as exc:
            logging.exception("Failed to check tape remaining", exc)
            response.response = INVALID_ARGUMENTS
        return response

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    known, remaining = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + remaining
    
    if not known.port:
        raise RuntimeWarning("Port must be provided...")
    serve(XPeelServer(), str(known.port))
