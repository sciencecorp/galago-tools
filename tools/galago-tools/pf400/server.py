from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.pf400_pb2 import Command, Config
from .driver import Pf400Driver
import argparse
from typing import Optional, Union
from tools.grpc_interfaces.tool_base_pb2 import ExecuteCommandReply, SUCCESS, ERROR_FROM_TOOL
from google.protobuf.struct_pb2 import Struct
import logging

class Pf400Server(ToolServer):
    toolType = "pf400"

    def __init__(self) -> None:
        super().__init__()
        self.driver: Pf400Driver
        self.sequence_location: str
        self.plate_handling_params: dict[str, dict[str, Union[Command.GraspPlate, Command.ReleasePlate]]] = {}
        self.waypoints: dict[str, dict[str, Union[Command.GraspPlate, Command.ReleasePlate]]] = {}
    def initialize(self) -> None:
        super().initialize()


    def Move(self, params: Command.Move) -> None:
        """Execute a move command with the given coordinate and motion profile."""
        coordinate = params.waypoint
        motion_profile = getattr(params, 'motion_profile_id', None)

        if motion_profile:
            self.driver.register_motion_profile(
                profile=motion_profile
            )
        else:
            profile_id = 1
        self.driver.movej(coordinate, motion_profile=profile_id)

    def retrieve_plate(
        self,
        source_nest: str,
        grasp_params: Optional[Command.GraspPlate] = None,
        nest_offset: tuple[float, float, float] = (0, 0, 0),
        motion_profile_id: int = 1,
        grip_width: int = 0,
    ) -> None:
        """Retrieve a plate from the specified coordinates."""
        grasp: Command.GraspPlate
        if not grasp_params:
            grasp = Command.GraspPlate(width=130, force=15, speed=10)
        else:
            grasp = grasp_params

        adjust_gripper = Command.ReleasePlate(width=grip_width or 140, speed=10)

        # Add offset to coordinates
        coords = source_nest.split()
        adjusted_coords = [float(coords[i]) + nest_offset[i] for i in range(3)]
        adjusted_coords.extend([float(x) for x in coords[3:]])
        adjusted_nest = ' '.join(map(str, adjusted_coords))

        self.runSequence([
            adjust_gripper,
            Command.Move(waypoint=adjusted_nest, motion_profile_id=motion_profile_id),
            grasp,
        ])

    def dropoff_plate(
        self,
        destination_nest: str,
        release_params: Optional[Command.ReleasePlate] = None,
        nest_offset: tuple[float, float, float] = (0, 0, 0),
        motion_profile_id: int = 1,
        grip_width: int = 0,
    ) -> None:
        """Drop off a plate at the specified coordinates."""
        release: Command.ReleasePlate
        if not release_params:
            release = Command.ReleasePlate(width=140, speed=10)
        else:
            release = release_params

        # Add offset to coordinates
        coords = destination_nest.split()
        adjusted_coords = [float(coords[i]) + nest_offset[i] for i in range(3)]
        adjusted_coords.extend([float(x) for x in coords[3:]])
        adjusted_nest = ' '.join(map(str, adjusted_coords))

        self.runSequence([
            Command.Move(waypoint=adjusted_nest, motion_profile_id=motion_profile_id),
            release,
        ])
    def Jog(self, params: Command.Jog) -> None:
        """Handle jog command from UI"""
        logging.info(f"Jogging {params.axis} by {params.distance}")
        if not self.driver:
            raise Exception("Driver not initialized")
        self.driver.jog(params.axis, params.distance)

    def Transfer(self, params: Command.Transfer) -> None:
        """Execute a transfer between source and destination coordinates."""
        profile_id = getattr(params, 'motion_profile_id', 1)
        
        self.retrieve_plate(
            source_nest=params.source_nest.nest,
            grasp_params=params.grasp_params,
            nest_offset=(
                params.source_nest.x_offset,
                params.source_nest.y_offset,
                params.source_nest.z_offset,
            ),
            motion_profile_id=profile_id,
            grip_width=params.grip_width,
        )

        self.dropoff_plate(
            destination_nest=params.destination_nest.nest,
            release_params=params.release_params,
            nest_offset=(
                params.destination_nest.x_offset,
                params.destination_nest.y_offset,
                params.destination_nest.z_offset,
            ),
            motion_profile_id=profile_id,
            grip_width=params.grip_width,
        )
    def Wait(self, params: Command.Wait) -> None:
        self.driver.wait(duration=params.duration)

    def GetCurrentLocation(self, params: Command.GetCurrentLocation) -> ExecuteCommandReply:
        """Get current robot position"""
        response = ExecuteCommandReply()
        response.return_reply = True
        response.response = SUCCESS
        try:
            if not self.driver:
                raise Exception("Driver not initialized")
            position = self.driver.wherej()  # Using the direct wherej command from driver
            
            # Create meta_data with the location information
            meta = Struct()
            meta.update({"location": position})
            response.meta_data.CopyFrom(meta)
            
            return response
        except Exception as e:
            logging.error(f"Error getting position: {e}")
            response.response = ERROR_FROM_TOOL
            response.error_message = str(e)
            return response

    def RunSequence(self, params: Command.RunSequence) -> None:
        """Execute a sequence of commands."""
        if not self.driver:
            raise Exception("Driver not initialized")

        sequence = {} # TODO: Implement sequence loading
        
        for command in sequence:
            # Extract command type and parameters
            command_type = command["command_type"]
            command_params = command["params"]
            
            # Convert command type to method name (e.g., "move" -> "Move")
            method_name = command_type.capitalize()
            method = getattr(self, method_name, None)
            
            if not method:
                raise Exception(f"Unknown command type: {command_type}")
            
            # Create Command object with parameters
            command_obj = Command()
            command_field = getattr(command_obj, command_type)
            
            # Parse parameters into protobuf message
            for key, value in command_params.items():
                setattr(command_field, key, value)
            
            # Execute the command
            method(command_field)

    def estimateRunSequence(self, sequence: list[Command]) -> int:
        return 1

    def EstimateGetCurrentLocation(self, params: Command.GetCurrentLocation) -> int:
        return 1

    def EstimateMove(self, params: Command.Move) -> int:
        return 1
    
    def EstimateTransfer(self, params: Command.Transfer) -> int:
        return 1
    
    def EstimateJog(self, params: Command.Jog) -> int:
        return 1

    def EstimateWait(self, params: Command.Wait) -> int:
        return 1
    
    def _configure(self, config: Config) -> None:
        """Configure the robot driver with the given configuration."""
        self.config = config
        if self.driver:
            self.driver.close()
        self.driver = Pf400Driver(
            tcp_host=self.config.host,
            tcp_port=self.config.port
        )
        self.driver.initialize()
    
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    serve(Pf400Server(), str(args.port))
