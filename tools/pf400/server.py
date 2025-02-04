from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.pf400_pb2 import Command, Config
from tools.labware import LabwareDb, Labware
from .driver import Pf400Driver
import argparse
from typing import Optional, Union
from tools.grpc_interfaces.tool_base_pb2 import ExecuteCommandReply, SUCCESS, ERROR_FROM_TOOL
from google.protobuf.struct_pb2 import Struct
import logging
from tools.pf400.waypoints_models import (
    Waypoints,
    MotionProfile,
    Grip
)       
import json 

class Pf400Server(ToolServer):
    toolType = "pf400"

    def __init__(self) -> None:
        super().__init__()
        self.config : Config 
        self.driver: Pf400Driver
        self.waypoints: Waypoints
        self.sequence_location : str
        self.plate_handling_params : dict[str, dict[str, Union[Command.GraspPlate, Command.ReleasePlate]]] = {}

    def _configure(self, request: Config) -> None:
        self.config = request
        if self.driver:
            self.driver.close()
        self.driver = Pf400Driver(
            tcp_host=request.host,
            tcp_port=request.port
        )
        self.driver.initialize()
        logging.info("Successfully connected to PF400")

    def LoadWaypoints(self, params: Command.LoadWaypoints) -> None:
        #Locations 
    
        locations_dict : Waypoints = json.loads(params.locations.to_json())
        logging.info(locations_dict)
        self.waypoints = Waypoints.parse_obj(locations_dict)
        logging.info("Locations loaded")

        #Plate handling params 
        plate_handling_params : dict[str, Grip] = json.loads(params.plate_handling_params.to_json())
        plate_handling_params = Grip.parse_obj(plate_handling_params)

        if "landscape" not in plate_handling_params.grip_params or "portrait" not in plate_handling_params.grip_params:
            raise KeyError("missing lanndscape or portrait grip settings")
        
        for grip in plate_handling_params:
            plate_width = grip["width"]
            grip_force = grip["force"]
            grip_speed = grip["speed"]
            self.plate_handling_params[grip] = {
                "grasp": Command.GraspPlate(width=plate_width, force=grip_force, speed=grip_speed),
                "release": Command.ReleasePlate(width=plate_width, speed=grip_speed)
            }

        #Load and register profiles 
        motion_profiles_list : list[MotionProfile] = json.loads(params.motion_profiles.to_json())
        motion_profiles_list = MotionProfile.parse_obj(motion_profiles_list)

        for motion_profile in motion_profiles_list:
            self.driver.register_motion_profile(str(motion_profile))

    def Retract(self,params: Command.Retract) -> None:
        waypoint_name = "retract"
        if waypoint_name not in self.waypoints.locations:
            raise KeyError("Retract location not found")
        waypoint_loc = self.waypoints.locations[waypoint_name].loc
        current_loc_array = self.driver.wherej().split(" ")
        #Retract the arm while keeping the z height, gripper width and rail constant
        #current_loc_array[1] is the z height, current_loc_array[6] is the gripper (regardless of the number of joints)
        if self.config.joints == 5:
           new_loc = f"{current_loc_array[1]} {waypoint_loc.vec[1]} {waypoint_loc.vec[2]} {waypoint_loc.vec[3]} {current_loc_array[5]}"
        else:
            new_loc = f"{current_loc_array[1]} {waypoint_loc.vec[1]} {waypoint_loc.vec[2]} {waypoint_loc.vec[3]} {current_loc_array[5]} {current_loc_array[6]}"
        self.driver.movej(new_loc,  motion_profile=params.profile_id)

    def Release(self, params: Command.Release) -> None:
        self.driver.safe_free()

    def Engage(self, params: Command.Engage) -> None:
        self.driver.unfree()

    def Move(self, params: Command.Move) -> None:
        """Execute a move command with the given coordinate and motion profile."""
        location_name = params.name 
        if location_name not in self.waypoints.locations:
            raise KeyError("Location not found: " + location_name)
        location= self.waypoints.locations[location_name]
        self.driver.movej(location, motion_profile=params.motion_profile_id)

    def moveTo(self, location: str, offset: tuple[float, float, float] = (0, 0, 0), motion_profile_id: int = 1) -> None:
        """Move to a location with optional offset"""
        coords = location.split()
        adjusted_coords = [float(coords[i]) + offset[i] for i in range(3)]
        adjusted_coords.extend([float(x) for x in coords[3:]])
        adjusted_location = ' '.join(map(str, adjusted_coords))
        self.driver.movej(adjusted_location, motion_profile=motion_profile_id)

    def GraspPlate(self, params: Command.GraspPlate) -> None:
        self.driver.graspplate(params.width, params.force, params.speed)

    def ReleasePlate(self, params: Command.ReleasePlate) -> None:
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

    def RetrievePlate(self, params: Command.RetrievePlate) -> None:
        labware:Labware = self.all_labware.get_labware(params.labware)
        offset = (0,0,labware.zoffset)
        self.retrieve_plate(source_nest=params.location, motion_profile_id=params.motion_profile_id, nest_offset=offset)

    def DropOffPlate(self, params: Command.DropOffPlate) -> None:
        labware:Labware = self.all_labware.get_labware(params.labware)
        offset = (0,0,labware.zoffset)
        self.dropoff_plate(destination_nest=params.location, motion_profile_id=params.motion_profile_id, nest_offset=offset)

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

    def PickLid(self, params: Command.PickLid) -> None:
        labware:Labware = self.all_labware.get_labware(params.labware)
        if params.location not in self.waypoints.nests:
            raise KeyError("Nest not found: " + params.location)
        grasp: Command.GraspPlate
        tmp_grasp: Union[Command.GraspPlate,Command.ReleasePlate] = self.plate_handling_params[
            self.waypoints.nests[params.location].orientation
        ]["grasp"]
        if isinstance(tmp_grasp, Command.GraspPlate):
            grasp = tmp_grasp
            grasp.force = 15
            grasp.speed = 10
        else:
            raise Exception("Invalid grasp params")

        tmp_adjust_gripper = self.plate_handling_params[self.waypoints.nests[params.location].orientation]["release"]
        if isinstance(tmp_adjust_gripper, Command.ReleasePlate):
            adjust_gripper = tmp_adjust_gripper
        else:
            raise Exception("Invalid release params")

        if params.pick_from_plate:
            lid_height = labware.height - 4 + labware.plate_lid_offset
        else:
            lid_height = labware.plate_lid_offset + labware.lid_offset
            
        self.runSequence(
            [
                adjust_gripper,
                Command.Approach(
                    nest=params.location,
                    z_offset=lid_height,
                    motion_profile_id=params.motion_profile_id,
                    ignore_safepath="false"
                ),
                grasp,
                Command.Approach(
                    nest=params.location,
                    z_offset=lid_height + 8,
                    motion_profile_id=params.motion_profile_id,
                    ignore_safepath="true"
                ),
            ]
        )
    
    def PlaceLid(self, params: Command.PlaceLid) -> None:
        labware:Labware = self.all_labware.get_labware(params.labware)
        if params.location not in self.waypoints.nests:
            raise KeyError("Nest not found: " + params.location)
        
        release: Command.ReleasePlate
        tmp_release: Union[Command.GraspPlate, Command.ReleasePlate] = self.plate_handling_params[
            self.waypoints.nests[params.location].orientation
        ]["release"]
        if isinstance(tmp_release, Command.ReleasePlate):
            release = tmp_release
        else:
            raise Exception("Invalid release params")
        
        logging.info("Place lid params are "+ str(params.place_on_plate))
        if params.place_on_plate:
            lid_height = labware.height - 4 + labware.plate_lid_offset
        else:
            lid_height = labware.plate_lid_offset + labware.lid_offset

        self.runSequence(
            [
                Command.Approach(
                    nest=params.location,
                    z_offset=lid_height,
                    motion_profile_id=params.motion_profile_id,
                    ignore_safepath="true"
                ),
                release,
                Command.Approach(
                    nest=params.location,
                    z_offset=lid_height + 8,
                    motion_profile_id=params.motion_profile_id,
                    ignore_safepath="true"
                ),
            ]
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
    
    def estimateRelease(self, params: Command.Release) -> int:
        return 1

    def estimateEngage(self, params: Command.Engage) -> int:
        return 1

    def estimateRetract(self, params: Command.Retract) -> int:
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
    
    def EstimatePickLid(self, params: Command.PickLid) -> int:
        return 1
    
    def EstimatePlaceLid(self, params: Command.PlaceLid) -> int:
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
