from tools.base_server import ABCToolDriver
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.custom_tool_pb2 import Command, Config
from tools.grpc_interfaces.tool_base_pb2 import ExecuteCommandReply
import argparse 
from tools.utils import struct_to_dict
class ExampleDriver(ABCToolDriver):
    def __init__(self, robot_ip: str, robot_port: int) -> None:
        super().__init__(robot_ip, robot_port)
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
    toolType = "example"
    driver: ExampleDriver

    def __init__(self) -> None:
        super().__init__()
        self.driver: ExampleDriver
        self.process_images: bool = True 

    #Abstract class where initialize/connect logic should be implemented
    def _configure(self, request: Config) -> None:
        self.config = struct_to_dict(request)
        
        self.driver = ExampleDriver(self.config.get("ip"), self.config.get("port"))
        self.driver.ping()
        self.driver.connect()

    
    #Abstract class to implement the logic for the command
    def ExecuteCommand(self, params:Command.ExecuteCommand) -> None:
        command = params.command
        params = struct_to_dict(params.params)
        args = struct_to_dict(params.args)

        print(f"Executing command: {command} with args: {args}")
        
        if command == "set_temperature":
            self.driver.set_temperature(args.get("temperature"), args.get("time"))
        elif command == "move_to_location":
            self.driver.move_to_location(args.get("location"))
        else:
            print(f"Unknown command: {command}")

    def EstimateExecuteCommand(self, params:Command.ExecuteCommand) -> int:
        command = params.command
        params = struct_to_dict(params.params)
        args = struct_to_dict(params.args)

        print(f"Estimating command: {command} with args: {args}")
        
        if command == "set_temperature":
            return 1
        elif command == "move_to_location":
            return 10
        else:
            print(f"Unknown command: {command}")
            return 0