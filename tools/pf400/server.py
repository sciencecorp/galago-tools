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
        self.waypoints: dict = {}
        # Store mappings for motion profiles, grip params, and labware
        self.motion_profile_map: dict[int, int] = {}  # Map DB ID to profile ID
        self.grip_params_map: dict[int, dict[str, int]] = {}  # Map DB ID to grip params
        self.labware_map: dict[int, str] = {}  # Map DB ID to labware name

    def _configure(self, request: Config) -> None:
        """Configure the PF400 server with the provided configuration."""
        try:
            # Reset all mappings
            self.motion_profile_map = {}
            self.grip_params_map = {}
            self.labware_map = {}
            self.waypoints = {}

            # If in simulation mode, don't attempt hardware connection
            if self.simulated:
                logging.info("Configuring PF400 in simulation mode")
                return

            # Configure hardware connection
            try:
                self.driver = Pf400Driver(
                    tcp_host=request.host,
                    tcp_port=request.port
                )
                # Initialize the driver
                self.driver.initialize()
                # Test connection by getting current position
                self.driver.wherej()
                logging.info("Successfully connected to PF400")
            except Exception as e:
                logging.error(f"Failed to connect to PF400: {e}")
                raise

        except Exception as e:
            logging.error(f"Error configuring PF400: {str(e)}")
            # Reset all mappings on error
            self.motion_profile_map = {}
            self.grip_params_map = {}
            self.labware_map = {}
            self.waypoints = {}
            raise

    def _map_motion_profile(self, db_id: int) -> int:
        """Map database motion profile ID to robot profile ID"""
        if db_id in self.motion_profile_map:
            return self.motion_profile_map[db_id]
        logging.warning(f"Motion profile ID {db_id} not found in mapping, using default profile 1")
        return 1

    def _map_grip_params(self, db_id: int) -> dict[str, int]:
        """Map database grip params ID to robot grip parameters"""
        if db_id in self.grip_params_map:
            return self.grip_params_map[db_id]
        logging.warning(f"Grip params ID {db_id} not found in mapping, using defaults")
        return {"width": 130, "force": 15, "speed": 10}

    def _map_labware(self, db_id: int) -> str:
        """Map database labware ID to labware name"""
        if db_id in self.labware_map:
            return self.labware_map[db_id]
        logging.warning(f"Labware ID {db_id} not found in mapping, using 'default'")
        return "default"

    def Free(self, params: Command.Release) -> None:
        self.driver.safe_free()

    def UnFree(self, params: Command.Engage) -> None:
        self.driver.unfree()

    def Move(self, params: Command.Move) -> None:
        """Execute a move command with the given coordinate and motion profile."""
        coordinate = params.waypoint
        motion_profile = getattr(params, 'motion_profile_id', None)

        if motion_profile:
            logging.info(f"Motion profile ID {motion_profile} found in params")
            # Map the motion profile ID if it's from the database
            profile_id = self._map_motion_profile(motion_profile)
            logging.info(f"Registering motion profile {profile_id} for DB ID {motion_profile}")
            # self.driver.register_motion_profile(str(profile_id))
        else:
            profile_id = 1
        self.driver.movej(coordinate, motion_profile=profile_id)

    def Approach(self, params: Command.Approach) -> None:
        nest_name = params.nest
        if nest_name not in self.waypoints:
            raise KeyError("Nest not found: " + nest_name)
        if not params.motion_profile_id:
            params.motion_profile_id = 1
        nest_def = self.waypoints.nests[nest_name]
        logging.info("Moving to nest %s at %s", nest_name, nest_def.loc)
        logging.info(type(params.ignore_safepath))
        logging.info("Ignore path is "+ str(params.ignore_safepath))
        # It appears the monomer approach paths are actually reversed "leave" paths

        ignore_path = False
        if params.ignore_safepath == "true" or params.ignore_safepath == "True":
            ignore_path = True
        if ignore_path is not True:
            logging.info("Going through safe path")
            self.movePath(
                self.nestPath(
                    nest_def,
                    offset=(
                        params.x_offset,
                        params.y_offset,
                        params.z_offset,
                    ),
                )[::-1],
                motion_profile_id=params.motion_profile_id,
            )

        self.moveTo(
            nest_def.loc,
            offset=(
                params.x_offset,
                params.y_offset,
                params.z_offset,
            ),
            motion_profile_id=params.motion_profile_id,
        )
    
    def Leave(self, params: Command.Leave) -> None:
        nest_name = params.nest
        if nest_name not in self.waypoints.nests:
            raise KeyError("Nest not found: " + nest_name)
        if not params.motion_profile_id:
            params.motion_profile_id = 1
        nest_def = self.waypoints.nests[nest_name]
        logging.info("Leaving nest %s at %s", nest_name, nest_def.loc)
        self.movePath(
            self.nestPath(
                nest_def,
                offset=(
                    params.x_offset,
                    params.y_offset,
                    params.z_offset,
                ),
            ),
            motion_profile_id=params.motion_profile_id,
        )

    def GraspPlate(self, params: Command.GraspPlate) -> None:
        # If params has an ID, map it to the actual grip parameters
        if hasattr(params, 'id'):
            grip_params = self._map_grip_params(params.id)
            self.driver.graspplate(grip_params["width"], grip_params["force"], grip_params["speed"])
        else:
            self.driver.graspplate(params.width, params.force, params.speed)

    def ReleasePlate(self, params: Command.ReleasePlate) -> None:
        # If params has an ID, map it to the actual grip parameters
        if hasattr(params, 'id'):
            grip_params = self._map_grip_params(params.id)
            self.driver.releaseplate(grip_params["width"], grip_params["speed"])
        else:
            self.driver.releaseplate(params.width, params.speed)

    def retrieve_plate(
        self,
        source_nest: str,
        grasp_params: Optional[Command.GraspPlate] = None,
        nest_offset: tuple[float, float, float] = (0, 0, 0),
        motion_profile_id: int = 1,
        grip_width: int = 0,
        labware_id: Optional[int] = None,
    ) -> None:
        """Retrieve a plate from the specified coordinates."""
        # Map the motion profile ID if it's from the database
        profile_id = self._map_motion_profile(motion_profile_id)

        grasp: Command.GraspPlate
        if not grasp_params:
            grasp = Command.GraspPlate(width=130, force=15, speed=10)
        else:
            if hasattr(grasp_params, 'id'):
                grip_params = self._map_grip_params(grasp_params.id)
                grasp = Command.GraspPlate(**grip_params)
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
            Command.Move(waypoint=adjusted_nest, motion_profile_id=profile_id),
            grasp,
        ])

    def dropoff_plate(
        self,
        destination_nest: str,
        release_params: Optional[Command.ReleasePlate] = None,
        nest_offset: tuple[float, float, float] = (0, 0, 0),
        motion_profile_id: int = 1,
        grip_width: int = 0,
        labware_id: Optional[int] = None,
    ) -> None:
        """Drop off a plate at the specified coordinates."""
        # Map the motion profile ID if it's from the database
        profile_id = self._map_motion_profile(motion_profile_id)

        release: Command.ReleasePlate
        if not release_params:
            release = Command.ReleasePlate(width=140, speed=10)
        else:
            if hasattr(release_params, 'id'):
                grip_params = self._map_grip_params(release_params.id)
                release = Command.ReleasePlate(width=grip_params["width"], speed=grip_params["speed"])
            else:
                release = release_params

        # Add offset to coordinates
        coords = destination_nest.split()
        adjusted_coords = [float(coords[i]) + nest_offset[i] for i in range(3)]
        adjusted_coords.extend([float(x) for x in coords[3:]])
        adjusted_nest = ' '.join(map(str, adjusted_coords))

        self.runSequence([
            Command.Move(waypoint=adjusted_nest, motion_profile_id=profile_id),
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
        logging.info("Running sequence")
        """Execute a sequence of commands."""
        if not self.driver:
            raise Exception("Driver not initialized")

        sequence_name = params.sequence_name
        logging.info(f"Looking for sequence '{sequence_name}' in waypoints")
        logging.info(f"Available waypoints: {list(self.waypoints.keys())}")
        logging.info(f"Waypoints content: {self.waypoints}")
        
        if sequence_name not in self.waypoints:
            raise Exception(f"Sequence '{sequence_name}' not found in waypoints")
        
        sequence = self.waypoints[sequence_name]
        logging.info(f"Found sequence {sequence_name}")
        logging.info(f"Sequence type: {type(sequence)}")
        logging.info(f"Sequence content: {sequence}")
        
        if not isinstance(sequence, list):
            raise Exception(f"Invalid sequence format for '{sequence_name}'")
        
        for command in sequence:
            if not isinstance(command, dict) or 'command' not in command or 'params' not in command:
                raise Exception(f"Invalid command format in sequence '{sequence_name}'")
            
            command_type = command["command"]
            command_params = command["params"]
            
            # Convert command type to method name (e.g., "move" -> "Move")
            method_name = command_type.capitalize()
            method = getattr(self, method_name, None)
            
            if not method:
                raise Exception(f"Unknown command type: {command_type}")
            
            # Create Command object with parameters
            command_obj = Command()
            command_field = getattr(command_obj, command_type)
            
            # For move commands, ensure waypoint exists
            if command_type == "move" and "waypoint" in command_params:
                waypoint = command_params["waypoint"]
                if waypoint not in self.waypoints:
                    raise Exception(f"Waypoint '{waypoint}' not found")
                command_params["waypoint"] = self.waypoints[waypoint]
            
            # Parse parameters into protobuf message
            for key, value in command_params.items():
                setattr(command_field, key, value)
            
            # Execute the command
            method(command_field)

    def GetWaypoints(self, params: Command.GetWaypoints) -> ExecuteCommandReply:
        """Debug command to return current waypoints and mappings"""
        response = ExecuteCommandReply()
        response.return_reply = True
        response.response = SUCCESS
        
        try:
            meta = Struct()
            meta.update({
                "motion_profiles": str(self.motion_profile_map),
                "grip_params": str(self.grip_params_map),
                "labware": str(self.labware_map),
                "config_waypoints": str(getattr(self.config, 'waypoints', None))
            })
            response.meta_data.CopyFrom(meta)
            return response
        except Exception as e:
            logging.error(f"Error getting waypoints: {e}")
            response.response = ERROR_FROM_TOOL
            response.error_message = str(e)
            return response
    
    def LoadWaypoints(self, params: Command.LoadWaypoints) -> None:
        """Load all waypoints and parameter mappings in a single call"""
        logging.info("Loading waypoints")
        try:
            # Reset all mappings if no waypoints are provided
            if not params.waypoints:
                self.motion_profile_map = {}
                self.grip_params_map = {}
                self.labware_map = {}
                self.waypoints = {}
                return
            
            logging.info(f"Processing {len(params.waypoints)} waypoint configurations")
            for waypoint_config in params.waypoints:
                waypoint_type = waypoint_config.WhichOneof('waypoint_type')
                logging.info(f"Processing waypoint type: {waypoint_type}")
                
                if waypoint_type == 'motion_profile':
                    profile = waypoint_config.motion_profile
                    self.motion_profile_map[profile.id] = profile.profile_id
                    logging.info(f"Mapped motion profile {profile.profile_id} for DB ID {profile.id}")

                elif waypoint_type == 'grip_param':
                    param = waypoint_config.grip_param
                    self.grip_params_map[param.id] = {
                        'width': param.width,
                        'force': param.force,
                        'speed': param.speed
                    }
                    logging.info(f"Loaded grip params for DB ID {param.id}")

                elif waypoint_type == 'labware':
                    labware = waypoint_config.labware
                    self.labware_map[labware.id] = labware.name
                    logging.info(f"Mapped labware ID {labware.id} to name {labware.name}")
                
                elif waypoint_type == 'location':
                    location = waypoint_config.location
                    self.waypoints[location.name] = location.location
                    logging.info(f"Added location {location.name}: {location.location}")

                elif waypoint_type == 'sequence':
                    sequence = waypoint_config.sequence
                    logging.info(f"Loading sequence: {sequence.name}")
                    logging.info(f"Sequence commands type: {type(sequence.commands)}")
                    logging.info(f"Sequence commands: {sequence.commands}")
                    
                    # Convert sequence commands to proper dictionary format
                    formatted_commands = []
                    for cmd in sequence.commands:
                        cmd_type = cmd.WhichOneof('command')
                        if cmd_type:
                            cmd_params = getattr(cmd, cmd_type)
                            formatted_cmd = {
                                "command": cmd_type,
                                "params": {
                                    key: getattr(cmd_params, key)
                                    for key in cmd_params.DESCRIPTOR.fields_by_name.keys()
                                }
                            }
                            formatted_commands.append(formatted_cmd)
                    
                    self.waypoints[sequence.name] = formatted_commands
                    logging.info(f"Added sequence {sequence.name} with {len(formatted_commands)} commands")
                    logging.info(f"Stored sequence type: {type(self.waypoints[sequence.name])}")
                    logging.info(f"Stored sequence: {self.waypoints[sequence.name]}")
    
        except Exception as e:
            logging.error(f"Error loading waypoints and mappings: {str(e)}")
            raise
        
    def estimateFree(self, params: Command.Free) -> int:
        return 1

    def estimateUnFree(self, params: Command.UnFree) -> int:
        return 1
    
    def estimateGraspPlate(self, params: Command.GraspPlate) -> int:
        return 1

    def estimateReleasePlate(self, params: Command.ReleasePlate) -> int:
        return 1

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
    
    def EstimateApproach(self, params: Command.Approach) -> int:
        return 1
    
    def EstimateLeave(self, params: Command.Leave) -> int:
        return 1
    
    
    def EstimateGetWaypoints(self, params: Command.GetWaypoints) -> int:
        """Estimate duration for get_waypoints command"""
        return 1  # This is an instant operation

    def EstimateLoadWaypoints(self, params: Command.LoadWaypoints) -> int:
        """Estimate duration for load_waypoints command"""
        return 1  # This is an instant operation

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    serve(Pf400Server(), str(args.port))
