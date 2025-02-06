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
    MotionProfiles,
    Grips,
    Location,
    Labwares,
    ArmSequences
)       
import json 
from google.protobuf.struct_pb2 import Struct
import typing as t
from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct, Value, ListValue
from google.protobuf import json_format
from pydantic import TypeAdapter
from typing import List

class Pf400Server(ToolServer):
    toolType = "pf400"

    def __init__(self) -> None:
        super().__init__()
        self.config : Config 
        self.driver: Pf400Driver
        self.waypoints: Waypoints
        self.labwares : Labwares
        self.sequences : ArmSequences
        self.plate_handling_params : dict[str, dict[str, Union[Command.GraspPlate, Command.ReleasePlate]]] = {}

    def _configure(self, request: Config) -> None:
        self.config = request
        # if self.driver:
        #     self.driver.close()
        # self.driver = Pf400Driver(
        #     tcp_host=request.host,
        #     tcp_port=request.port
        # )
        #self.driver.initialize()
        logging.info("Successfully connected to PF400")

    def _getLocation(self, location_name: str) -> Location:
        location = next((x for x in self.waypoints.locations if x.name == location_name), None)
        if not location:
            raise Exception(f"Location '{location_name}' not found")
        return location
    
    def _getLabware(self, labware_name: str) -> Labware:
        labware = next((x for x in self.labwares.labwares if x.name == labware_name), None)
        if not labware:
            raise Exception(f"Labware '{labware_name}' not found")
        return labware
    
    def LoadWaypoints(self, params: Command.LoadWaypoints) -> None:
        logging.info("Loading waypoints")
        #Load locations
        waypoints_dictionary = json_format.MessageToDict(params.waypoints)
        locations_list : Waypoints = waypoints_dictionary.get("locations")
        self.waypoints = Waypoints.parse_obj({"locations": locations_list})
        logging.info(f"Loaded {len(self.waypoints.locations)} locations")
        
        #Load grips
        grips_list = waypoints_dictionary.get("grip_params")
        grip_params : Grips = Grips.parse_obj({"grip_params": grips_list})
        logging.info(f"Loaded {len(grip_params.grip_params)} grip parameters")
        for grip in grip_params.grip_params:
            self.plate_handling_params[grip.name] = {
                "grasp": Command.GraspPlate(width=grip.width, force=grip.force, speed=grip.speed),
                "release": Command.ReleasePlate(width=grip.width+10, speed=grip.speed)
            }

        #Load and register profiles 
        motion_profiles_list = waypoints_dictionary.get("motion_profiles")
        motion_profiles = MotionProfiles.parse_obj({"profiles": motion_profiles_list})
        logging.info(f"Loaded {len(motion_profiles.profiles)} motion profiles")
        for motion_profile in motion_profiles:
            self.driver.register_motion_profile(str(motion_profile))

        # #Load Sequences 
        sequences_list = waypoints_dictionary.get("sequences")
        sequences = ArmSequences.parse_obj({"sequences":sequences_list})
        self.sequences = sequences
        logging.info(f"Loaded {len(sequences.sequences)} sequences")


    def LoadLabware(self, params: Command.LoadLabware) -> None:
        labware_dictionary = MessageToDict(params.labwares)
        labware_lst = labware_dictionary.get("labwares")
        self.all_labware = Labwares.parse_obj({"labwares": labware_lst})
        logging.info(f"Loaded {len(self.all_labware.labwares)} labwares")
        
    def Retract(self,params: Command.Retract) -> None:
        waypoint_name = "Retract"
        if waypoint_name not in self.waypoints.locations:
            raise KeyError("Retract location not found. Please add a retract (unwind) location to the waypoints. Height or rail position does not matter.")
        waypoint_loc = self._getLocation(waypoint_name).coordinates
        current_loc_array = self.driver.wherej().split(" ")
        #Retract the arm while keeping the z height, gripper width and rail constant
        if self.config.joints == 5:
           new_loc = f"{current_loc_array[1]} {waypoint_loc.vec[1]} {waypoint_loc.vec[2]} {waypoint_loc.vec[3]} {current_loc_array[5]}"
        else:
            new_loc = f"{current_loc_array[1]} {waypoint_loc.vec[1]} {waypoint_loc.vec[2]} {waypoint_loc.vec[3]} {current_loc_array[5]} {current_loc_array[6]}"
        logging.info(f"Retracting to {new_loc}")
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
    ) -> None:
        if source_nest not in self.waypoints.nests:
            raise KeyError("Nest not found: " + source_nest)
        safe_point: str = self.waypoints.nests[source_nest].safe_loc
        grasp: Command.GraspPlate
        if not grasp_params or (grasp_params.width == 0):
            tmp_grasp: Union[Command.GraspPlate,Command.ReleasePlate] = self.plate_handling_params[
                self.waypoints.nests[source_nest].orientation
            ]["grasp"]
            if isinstance(tmp_grasp, Command.GraspPlate):
                grasp = tmp_grasp
            else:
                raise Exception("Invalid grasp params")
        else:
            grasp = grasp_params
        if grip_width > 0:
            adjust_gripper = Command.ReleasePlate(width=grip_width, speed=10)
        else:
            tmp_adjust_gripper = self.plate_handling_params[
                self.waypoints.nests[source_nest].orientation
            ]["release"]
            if isinstance(tmp_adjust_gripper, Command.ReleasePlate):
                adjust_gripper = tmp_adjust_gripper
            else:
                raise Exception("Invalid release params")
        self.runSequence(
            [
                Command.Move(waypoint=safe_point, motion_profile_id=1),
                adjust_gripper,
                # Command.Approach(
                #     nest=source_nest,
                #     x_offset=nest_offset[0],
                #     y_offset=nest_offset[1],
                #     z_offset=nest_offset[2],
                #     motion_profile_id=motion_profile_id,
                # ),
                grasp,
                # Command.Leave(
                #     nest=source_nest,
                #     x_offset=nest_offset[0],
                #     y_offset=nest_offset[1],
                #     z_offset=nest_offset[2],
                #     motion_profile_id=motion_profile_id,
                # ),
                Command.Move(waypoint=safe_point, motion_profile_id=2),
            ]
        )


    def dropoff_plate(
        self,
        destination_nest: str,
        release_params: Optional[Command.ReleasePlate] = None,
        nest_offset: tuple[float, float, float] = (0, 0, 0),
        motion_profile_id: int = 1,
        grip_width: int = 0,
    ) -> None:
        if destination_nest not in self.waypoints.nests:
            raise KeyError("Nest not found: " + destination_nest)
        safe_point: str = self.waypoints.nests[destination_nest].safe_loc
        release: Command.ReleasePlate
        if not release_params or (release_params.width == 0):
            tmp_release: Union[Command.GraspPlate , Command.ReleasePlate] = self.plate_handling_params[
                self.waypoints.nests[destination_nest].orientation
            ]["release"]
            if isinstance(tmp_release, Command.ReleasePlate):
                release = tmp_release
            else:
                raise Exception("Invalid release params")
        else:
            release = release_params
        self.runSequence(
            [
                Command.Move(waypoint=safe_point, motion_profile_id=1),
                # Command.Approach(
                #     nest=destination_nest,
                #     x_offset=nest_offset[0],
                #     y_offset=nest_offset[1],
                #     z_offset=nest_offset[2],
                #     motion_profile_id=motion_profile_id,
                # ),
                release,
                # Command.Leave(
                #     nest=destination_nest,
                #     x_offset=nest_offset[0],
                #     y_offset=nest_offset[1],
                #     z_offset=nest_offset[2],
                #     motion_profile_id=motion_profile_id,
                # ),
                Command.Move(waypoint=safe_point, motion_profile_id=1),
            ]
        )

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
                # Command.Approach(
                #     nest=params.location,
                #     z_offset=lid_height,
                #     motion_profile_id=params.motion_profile_id,
                #     ignore_safepath="false"
                # ),
                grasp,
                # Command.Approach(
                #     nest=params.location,
                #     z_offset=lid_height + 8,
                #     motion_profile_id=params.motion_profile_id,
                #     ignore_safepath="true"
                # ),
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
                # Command.Approach(
                #     nest=params.location,
                #     z_offset=lid_height,
                #     motion_profile_id=params.motion_profile_id,
                #     ignore_safepath="true"
                # ),
                release,
                # Command.Approach(
                #     nest=params.location,
                #     z_offset=lid_height + 8,
                #     motion_profile_id=params.motion_profile_id,
                #     ignore_safepath="true"
                # ),
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
        # logging.info(f"Looking for sequence '{sequence_name}' in waypoints")
        # logging.info(f"Available waypoints: {list(self.waypoints.keys())}")
        # logging.info(f"Waypoints content: {self.waypoints}")
        
        if sequence_name not in self.waypoints:
            raise Exception(f"Sequence '{sequence_name}' not found in waypoints")
        
        sequence = self.waypoints[sequence_name]
        # logging.info(f"Found sequence {sequence_name}")
        # logging.info(f"Sequence type: {type(sequence)}")
        # logging.info(f"Sequence content: {sequence}")
        
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

    def EstimatePickLid(self, params: Command.PickLid) -> int:
        return 1
    
    def EstimatePlaceLid(self, params: Command.PlaceLid) -> int:
        return 1

    def EstimateLoadWaypoints(self, params: Command.LoadWaypoints) -> int:
        return 1 
    
    def EstimateLoadLabware(self, params: Command.LoadLabware) -> int:
        return 1

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    serve(Pf400Server(), str(args.port))
