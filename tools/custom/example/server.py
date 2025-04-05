from tools.base_server import ABCToolDriver
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.custom_tool_pb2 import Command, Config
import argparse 
from tools.utils import struct_to_dict
import logging 
import os 

class ExampleDriver(ABCToolDriver):
    def __init__(self, robot_ip: str, robot_port: int) -> None:
        self.robot_ip = robot_ip
        self.robot_port = robot_port

    def ping(self) -> None:
        print(f"Pinging {self.robot_ip}:{self.robot_port}")
    
    def connect(self) -> None:
        print(f"Connecting to {self.robot_ip}:{self.robot_port}")
    
    def disconnect(self) -> None:
        print(f"Disconnecting from {self.robot_ip}:{self.robot_port}")

    def take_picture(self, name: str, path: str) -> None:
        print(f"Taking picture {name} at {path}")
    
    def set_temperature(self, temperature: float, time: int) -> None:
        print(f"Incubating at {temperature}°C for {time} seconds")

    def move_to_location(self, location: str) -> None:
        print(f"Moving to {location}")


class ExampleServer(ToolServer):
    toolType = "custom_tool"
    driver: ExampleDriver
    config: Config

    def __init__(self) -> None:
        super().__init__()
        self.driver: ExampleDriver

    #Abstract class where initialize/connect logic should be implemented
    def _configure(self, request: Config) -> None:
        self.config = request
        self.config_dict = struct_to_dict(request.config)
        self.driver = ExampleDriver(str(self.config_dict.get("ip")), int(self.config_dict.get("port")))
        self.driver.ping()
        self.driver.connect()
    
    #Abstract class to implement the logic for the command
    def RunCommand(self, params:Command.RunCommand) -> None:
        command = params.command
        params = struct_to_dict(params.params)

        print(f"Executing command: {command} with params: {params}")
        
        if command == "set_temperature":
            self.driver.set_temperature(params.get("temperature"), params.get("time"))
        elif command == "move_to_location":
            self.driver.move_to_location(params.get("location"))
        else:
            print(f"Unknown command: {command}")

    def EstimateRunCommand(self, params:Command.RunCommand) -> int:
        command = params.command
        params = struct_to_dict(params.params)

        print(f"Estimating command: {command} with params: {params}")
        
        if command == "set_temperature":
            return 1
        elif command == "move_to_location":
            return 10
        else:
            print(f"Unknown command: {command}")
            return 0
        

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    serve(ExampleDriver(),os.environ.get("PORT",str(args.port)))