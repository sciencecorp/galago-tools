import json 
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.pf400_pb2 import Command, Config
from .driver import Pf400Driver
import argparse
from typing import Optional, Union 
from tools.grpc_interfaces.tool_base_pb2 import ExecuteCommandReply, SUCCESS, ERROR_FROM_TOOL
from google.protobuf.struct_pb2 import Struct
import logging
from tools.pf400.waypoints_models import (
    Waypoints,
    MotionProfiles,
    MotionProfile,
    Grips,
    Grip,
    Location,
    Labwares,
    ArmSequences,
    ArmSequence,
    Coordinate,
    Labware
)       
from google.protobuf.json_format import MessageToDict
from google.protobuf import json_format
from google.protobuf import message
import typing as t  
from google.protobuf.json_format import Parse

#Default motion profiles
DEFAULT_MOTION_PROFILES : list[MotionProfile] = [
    #curved motion profile
    MotionProfile(
        name="default",
        id=1,
        speed=85,
        speed2=80,
        acceleration=60,
        deceleration=60,
        accel_ramp=0.1,
        decel_ramp=0.1,
        inrange=0,
        straight=0
    ), 
    #straight motion profile
    MotionProfile(
        name="default_straight",
        id=2,
        speed=85,
        speed2=80,
        acceleration=100,
        deceleration=100,
        accel_ramp=0.1,
        decel_ramp=0.1,
        inrange=0,
        straight=1
    ),
]


DEFAULT_PLATE_HANDLING_PARAMS : dict[str, dict[str, Union[Command.GraspPlate, Command.ReleasePlate]]]= {
    "landscape":
    {
        "grasp": Command.GraspPlate(width=122, force=15, speed=10),
        "release": Command.ReleasePlate(width=130, speed=10)
    },
    "portrait": {
        "grasp": Command.GraspPlate(width=86, force=15, speed=10),
        "release": Command.ReleasePlate(width=96, speed=10)
    }
}

class Pf400Server(ToolServer):
    toolType = "pf400"

    def __init__(self) -> None:
        super().__init__()
        self.config : Config 
        self.driver: Pf400Driver
        self.waypoints: Waypoints
        self.labwares : Labwares
        self.sequences : ArmSequences
        self.motion_profiles : MotionProfiles
        self.grips : Grips
        self.plate_handling_params : dict[str, dict[str, Union[Command.GraspPlate, Command.ReleasePlate]]] = {}

    def _configure(self, request: Config) -> None:
        self.config = request
        if self.driver:
            self.driver.close()
        self.driver = Pf400Driver(
            tcp_host=request.host,
            tcp_port=request.port,
            joints=request.joints,
            gpl_version=request.gpl_version,

        )
        self.driver.initialize()

    def _getGrip(self, grip_name:str) -> Grip:
        grip = next((x for x in self.grips.grip_params if x.name.lower() == grip_name.lower()), None)
        if not grip:
            raise RuntimeError(f"Grip {grip_name} not defined.")
        return grip

    def _getLocation(self, location_name: str) -> Optional[Location]:
        location = next((x for x in self.waypoints.locations if x.name.lower() == location_name.lower()), None)
        if not location:
            logging.warning(f"Location '{location_name.lower()}' not found")
        return location
    
    def _getLabware(self, labware_name: str) -> Labware:
        labware = next((x for x in self.labwares.labwares if x.name == labware_name), None)
        if not labware:
            raise Exception(f"Labware '{labware_name}' not found")
        return labware
    
    def _getSequence(self, sequence_name:str) -> ArmSequence: 
        sequence = next((x for x in self.sequences.sequences if x.name == sequence_name), None)
        if not sequence:
            raise Exception(f"Sequence '{sequence_name}' not found")
        logging.info(f"Found sequence! {sequence_name}")
        return sequence
    
    def _getProfileId(self, profile_name:str) -> int:
        try:
            logging.info(f"Searching for profile {profile_name}")
            profile = next((x for x in self.motion_profiles.profiles if x.name.lower() == profile_name.lower()), None)
            if not profile:
                error_message = f"Profile '{profile_name}' not found"
                logging.error(error_message)
                return 1 # Default to the first profile if not found
            return profile.id
        except Exception as e:
            logging.error(f"Error in _getProfileId: {str(e)}")
            raise


    def LoadWaypoints(self, params: Command.LoadWaypoints) -> None:
            logging.info("Loading waypoints")
            #Load locations
            waypoints_dictionary: dict[str, t.Any] = json_format.MessageToDict(params.waypoints)
            locations_list = waypoints_dictionary.get("locations", [])
            self.waypoints = Waypoints.parse_obj({"locations": locations_list})
            logging.info(f"Loaded {len(self.waypoints.locations)} locations")

            #Load grips
            grips_list = waypoints_dictionary.get("grip_params")
            grip_params : Grips = Grips.parse_obj({"grip_params": grips_list})
            logging.info(f"Loaded {len(grip_params.grip_params)} grip parameters")
            if len(grip_params.grip_params) == 0:
                logging.warning("No grip parameters found. Using default grip parameters.")
                self.plate_handling_params = DEFAULT_PLATE_HANDLING_PARAMS
            else:
                for grip in grip_params.grip_params:
                    self.plate_handling_params[grip.name.lower()] = {
                        "grasp": Command.GraspPlate(width=grip.width, force=grip.force, speed=grip.speed),
                        "release": Command.ReleasePlate(width=grip.width+10, speed=grip.speed)
                    }

            self.grips = grip_params

            logging.info(f"Loaded {len(self.plate_handling_params)} plate handling parameters") 
            logging.info(self.plate_handling_params)
            
            #Load and register profiles 
            motion_profiles_list = waypoints_dictionary.get("motion_profiles")
            if motion_profiles_list:
                for i, profile in enumerate(motion_profiles_list):
                    profile["id"] = i + 1
            motion_profiles = MotionProfiles.parse_obj({"profiles": motion_profiles_list})
            
            self.motion_profiles = motion_profiles
            logging.info(f"Loaded {len(motion_profiles.profiles)} motion profiles")
  
            if motion_profiles_list and len(motion_profiles_list) > 0:
                for motion_profile in motion_profiles.profiles:
                    logging.info(f"Registering motion profile {motion_profile.name}")
                    try:
                        profile_no_name = motion_profile.copy(deep=True)
                        profile_no_name.name = ""
                        self.driver.register_motion_profile(str(motion_profile))
                    except Exception as e:
                        logging.error(f"Error registering motion profile {motion_profile.name}: {e}")
                        raise Exception(f"Error registering motion profile {motion_profile.name}: {e}")
            else:
                #Register default motion profiles
                logging.info("No motion profiles loaded. Using default profiles.")
                for motion_profile in DEFAULT_MOTION_PROFILES:
                    logging.info(f"Registering default motion profiles {motion_profile.name}")
                    try:
                        #Remove name from the profile 
                        profile_no_name = motion_profile.copy(deep=True)
                        profile_no_name.name = ""
                        logging.info(profile_no_name)
                        self.driver.register_motion_profile(str(motion_profile))
                    except Exception as e:
                        logging.error(f"Error registering motion profile {motion_profile.name}: {e}")
                        raise Exception(f"Error registering motion profile {motion_profile.name}: {e}")
                
            # #Load Sequences 
            sequences_list = waypoints_dictionary.get("sequences")
            sequences = ArmSequences.parse_obj({"sequences":sequences_list})
            logging.info(f"Loaded {len(sequences.sequences)} sequences")
            self.sequences = sequences

    
    def LoadLabware(self, params: Command.LoadLabware) -> None:
        logging.info("Loading labware")
        labware_dictionary = MessageToDict(params.labwares)
        labware_lst = labware_dictionary.get("labwares")
        self.labwares = Labwares.parse_obj({"labwares": labware_lst})
        logging.info(f"Loaded {len(self.labwares.labwares)} labwares")

    def _unwind(self) -> None:
        location = next((x for x in self.waypoints.locations if x.name.lower() in {"unwind"}), None)

        if not location:
            raise KeyError("Unwind location not found. Please add a unwind location to the waypoints. Height or rail position does not matter.")
        
        waypoint_loc = location.coordinates
        current_loc_array = self.driver.wherej().split(" ")
        #Unwind the arm while keeping the z height, gripper width and rail constant
        if self.config.joints == 5:
           new_loc = f"{current_loc_array[1]} {waypoint_loc.vec[1]} {waypoint_loc.vec[2]} {waypoint_loc.vec[3]} {current_loc_array[5]}"
        else:
            new_loc = f"{current_loc_array[1]} {waypoint_loc.vec[1]} {waypoint_loc.vec[2]} {waypoint_loc.vec[3]} {current_loc_array[5]} {current_loc_array[6]}"
        self.driver.movej(new_loc,  motion_profile=1)

    def Unwind(self,params: Command.Unwind) -> None:
        self._unwind()

    def Release(self, params: Command.Release) -> None:
        self.driver.safe_free()

    def Engage(self, params: Command.Engage) -> None:
        self.driver.unfree()

    def moveTo(
        self,
        loc: Location,
        approach_height: float = 0, #Height to move to before moving to the specified location
        motion_profile_id: int = 1,
    ) -> None:
        if self.driver is None:
            return
        loc_type = loc.location_type
        if loc_type == "c":
            string_offset =  f"0 0 {approach_height} 0 0 0"
            if self.config.joints == 5:
                string_offset = " ".join(string_offset.split(" ")[:-1])
            self.driver.movec(
                str(loc.coordinates + Coordinate(string_offset)),
                motion_profile=motion_profile_id,
            )
        #For now we only handle a z offset for joints
        elif loc_type == "j":
            string_offset = f"{approach_height} 0 0 0 0 0"
            self.driver.movej(str(loc.coordinates + Coordinate(string_offset)), 
                                motion_profile=motion_profile_id)
        else:
            raise Exception("Invalid location type")
        
    def Move(self, params: Command.Move) -> None:
        """Execute a move command with the given coordinate and motion profile."""
        location = self._getLocation(params.location)
        profile_id = self._getProfileId(params.motion_profile)
        if location is None:
            raise Exception(f"Location '{params.location}' not found")
        self.moveTo(location, params.approach_height, motion_profile_id=profile_id)

    def GraspPlate(self, params: Command.GraspPlate) -> None:
        self.driver.graspplate(params.width, params.force, params.speed)

    def ReleasePlate(self, params: Command.ReleasePlate) -> None:
        self.driver.releaseplate(params.width, params.speed)

    def retrieve_plate(
        self,
        source_nest: str,
        grasp_params: Optional[Command.GraspPlate] = None,
        approach_height: float = 0,
        motion_profile: str = "default",
        grip_width: int = 0,
        labware_name: str = "",
    ) -> None:
        source_location = self._getLocation(source_nest)
        if not source_location:
            raise Exception(f"Location '{source_nest}' not found")

        labware = self._getLabware(f"{labware_name}")
        labware_offset = labware.z_offset
        labware_offset = int(labware_offset)
        grip_width = int(grip_width)
        approach_height = int(approach_height)
        grasp: Command.GraspPlate
        if not grasp_params or (grasp_params.width == 0):
            grap_param_exists = self.plate_handling_params.get(source_location.orientation.lower())
            if not grap_param_exists:
                raise Exception(f"Grasp params for {source_location.orientation.lower()} not found")
            tmp_grasp: Union[Command.GraspPlate,Command.ReleasePlate] = self.plate_handling_params[
                source_location.orientation.lower()
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
                source_location.orientation.lower()
            ]["release"]
            if isinstance(tmp_adjust_gripper, Command.ReleasePlate):
                adjust_gripper = tmp_adjust_gripper
            else:
                raise Exception("Invalid release params")
            
        pre_grip_sequence : t.List[message.Message] = []
        retrieve_sequence : t.List[message.Message] = []
        open_grip_width= self._getGrip(source_location.orientation).width + 10
        pre_grip_sequence.append(adjust_gripper)
        pre_grip_sequence.append(Command.Move(location=source_location.name, motion_profile=motion_profile, approach_height=approach_height))
        pre_grip_sequence.append(Command.Move(location=source_location.name, motion_profile=motion_profile, approach_height=labware_offset))
        retrieve_sequence.extend([
            grasp,  # Grasp the plate
            Command.Move(location=source_location.name, motion_profile=motion_profile, approach_height=approach_height)
        ])
        self.driver.state.gripper_axis_override_value = open_grip_width
        self.runSequence(pre_grip_sequence)
        self.driver.state.gripper_axis_override_value = None
        self.runSequence(retrieve_sequence)

    def dropoff_plate(
        self,
        destination_nest: str,
        release_params: Optional[Command.ReleasePlate] = None,
        approach_height: float = 0,
        motion_profile: str = "default",
        labware_name: str = "",
    ) -> None:
        dest_location = self._getLocation(destination_nest)
        if not dest_location:
            raise Exception(f"Location '{destination_nest}' not found")

        release: Command.ReleasePlate
        labware = self._getLabware(f"{labware_name}")
        labware_offset = int(labware.z_offset)

        if not release_params or (release_params.width == 0):
            release_param_exists = self.plate_handling_params.get(dest_location.orientation.lower())
            if not release_param_exists:
                raise Exception(f"Release params for {dest_location.orientation.lower()} not found")
            tmp_release: Union[Command.GraspPlate , Command.ReleasePlate] = self.plate_handling_params[
                dest_location.orientation.lower()
            ]["release"]
            if isinstance(tmp_release, Command.ReleasePlate):
                release = tmp_release
            else:
                raise Exception("Invalid release params")
        else:
            release = release_params

        dropoff_sequence :t.List[message.Message] = []
        post_dropoff_sequence: t.List[message.Message] = []
        
        dropoff_sequence.extend([
                Command.Move(location=dest_location.name, motion_profile=motion_profile, approach_height=int(approach_height)), #Move to the dest location plus offset
                Command.Move(location=dest_location.name, motion_profile=motion_profile,approach_height=labware_offset), #Move to the nest location down in a straight pattern
                release #release the plate
        ])

        post_dropoff_sequence.append(Command.Move(location=dest_location.name, motion_profile=motion_profile, approach_height=int(approach_height))) #Move to the approach offset

        self.runSequence(dropoff_sequence)
        self.driver.state.gripper_axis_override_value = self._getGrip(dest_location.orientation).width + 10
        self.runSequence(post_dropoff_sequence)
        self.driver.state.gripper_axis_override_value = None

    def RetrievePlate(self, params: Command.RetrievePlate) -> None:
        self.retrieve_plate(source_nest=params.location, motion_profile=params.motion_profile, approach_height=params.approach_height, labware_name=params.labware)

    def DropOffPlate(self, params: Command.DropOffPlate) -> None:
        self.dropoff_plate(destination_nest=params.location, motion_profile=params.motion_profile, approach_height=params.approach_height, labware_name=params.labware)

    def Jog(self, params: Command.Jog) -> None:
        """Handle jog command from UI"""
        if not self.driver:
            raise Exception("Driver not initialized")
        self.driver.jog(params.axis, params.distance)

    def Transfer(self, params: Command.Transfer) -> None:
        self.retrieve_plate(
            source_nest=params.source_nest,
            motion_profile = params.motion_profile,
            approach_height=5,
            labware_name=params.labware
        )
        self._unwind()
        self.dropoff_plate(
            destination_nest=params.destination_nest,
            motion_profile=params.motion_profile,
            approach_height=5,
            labware_name=params.labware
        )


    def _pick_lid(
        self,
        location_name: str,
        labware_name: str,
        pick_from_plate: bool = False,
        approach_height: float = 0,
        motion_profile: str = "default",
    ) -> None:
        location: Optional[Location] = self._getLocation(location_name)
        if not location:
            raise Exception(f"Location '{location_name}' not found")
        
        # Get labware
        labware: Labware = self._getLabware(labware_name)
        
        # Configure grip parameters
        grasp: Command.GraspPlate
        tmp_grasp: Union[Command.GraspPlate, Command.ReleasePlate] = self.plate_handling_params[
            location.orientation.lower()
        ]["grasp"]
        if isinstance(tmp_grasp, Command.GraspPlate):
            grasp = tmp_grasp
            grasp.force = 15
            grasp.speed = 10
        else:
            raise Exception("Invalid grasp params")
        
        # Configure release parameters
        tmp_adjust_gripper = self.plate_handling_params[location.orientation.lower()]["release"]
        if isinstance(tmp_adjust_gripper, Command.ReleasePlate):
            adjust_gripper = tmp_adjust_gripper
        else:
            raise Exception("Invalid release params")
        
        # Calculate lid height
        if pick_from_plate:
            lid_height = labware.height - 6 + labware.plate_lid_offset
        else:
            lid_height = labware.plate_lid_offset + labware.lid_offset
        
        # Define sequences
        pre_pick_sequence: t.List[message.Message] = []
        pick_sequence: t.List[message.Message] = []
        
        # Configure gripper width
        open_grip_width = self._getGrip(location.orientation).width + 10
        
        # Set gripper override
        self.driver.state.gripper_axis_override_value = open_grip_width
        
        pre_pick_sequence.append(adjust_gripper)
        pre_pick_sequence.append(Command.Move(location=location.name, motion_profile=motion_profile, 
                                            approach_height=int(labware.height + approach_height)))
        pre_pick_sequence.append(Command.Move(location=location.name, motion_profile=motion_profile, 
                                            approach_height=int(lid_height)))
        
        # Build pick sequence
        pick_sequence.extend([
            grasp,
            Command.Move(location=location.name, motion_profile=motion_profile, approach_height=int(labware.height + approach_height)),
        ])
        
        
        # Execute sequences
        self.runSequence(pre_pick_sequence)
        self.driver.state.gripper_axis_override_value = None
        self.runSequence(pick_sequence)


    def PickLid(self, params: Command.PickLid) -> None:
        self._pick_lid(
            location_name=params.location,
            labware_name=params.labware,
            pick_from_plate=params.pick_from_plate,
            approach_height=params.approach_height,
            motion_profile=params.motion_profile
        )
    

    def _place_lid(
        self,
        location_name: str,
        labware_name: str,
        place_on_plate: bool = False,
        approach_height: float = 0,
        motion_profile: str = "default",
    ) -> None:
        # Get location
        location: Optional[Location] = self._getLocation(location_name)
        if not location:
            raise Exception(f"Location '{location_name}' not found")
        
        # Get labware
        labware: Labware = self._getLabware(labware_name)
        
        # Configure release parameters
        release: Command.ReleasePlate
        tmp_release: Union[Command.GraspPlate, Command.ReleasePlate] = self.plate_handling_params[
            location.orientation.lower()
        ]["release"]
        if isinstance(tmp_release, Command.ReleasePlate):
            release = tmp_release
        else:
            raise Exception("Invalid release params")
        
        # Calculate lid height
        if place_on_plate:
            lid_height = labware.height - 6 + labware.plate_lid_offset
        else:
            lid_height = labware.plate_lid_offset + labware.lid_offset
        
        # Define sequences
        place_lid_sequence: t.List[message.Message] = []
        post_place_sequence: t.List[message.Message] = []

        place_lid_sequence.extend([
            Command.Move(location=location.name, motion_profile=motion_profile, 
                        approach_height=int(labware.height + approach_height)),  # Move to the location plus approach height
            Command.Move(location=location.name, motion_profile=motion_profile, 
                        approach_height=int(lid_height)),  # Move to the calculated height
            release,
        ])
        
        post_place_sequence.append(Command.Move(location=location.name, motion_profile=motion_profile, 
                                            approach_height=int(labware.height + approach_height)))

        self.runSequence(place_lid_sequence)
        open_grip_width = self._getGrip(location.orientation).width + 10
        self.driver.state.gripper_axis_override_value = open_grip_width
        self.runSequence(post_place_sequence)
        
        self.driver.state.gripper_axis_override_value = None
        
    def PlaceLid(self, params: Command.PlaceLid) -> None:
        """Place lid handler that delegates to the _place_lid implementation"""
        self._place_lid(
            location_name=params.location,
            labware_name=params.labware,
            place_on_plate=params.place_on_plate,
            approach_height=params.approach_height,
            motion_profile=params.motion_profile
        )

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

    def command_instance_from_name(self, command_name: str) -> Union[message.Message, t.Any]:
        command_descriptors = Command.DESCRIPTOR.fields_by_name
        command_dictionary = dict()
        for (field_name, field_descriptor) in command_descriptors.items():
            if field_descriptor.message_type:
                if field_name not in command_dictionary:
                    command_dictionary[field_name] = field_descriptor.message_type.name
        
        return command_dictionary[command_name]

    def RunSequence(self, params: Command.RunSequence) -> None:
        commandSequence : list[message.Message] = list()
        sequence = self._getSequence(params.sequence_name)
        logging.info(f"Sequence has {len(sequence.commands)} commands")
        for arm_command in sequence.commands:
            command_params :t.Any = arm_command.params

            command_name :str = arm_command.command
            command_type : t.Any = self.command_instance_from_name(command_name)
            command : t.Any  = getattr(Command, command_type)

            if command_name == 'dropoff_plate' or command_name == 'retrieve_plate'  or command_name == 'pick_lid' or command_name == 'place_lid':
                if params.labware is not None:
                    command_params["labware"] = params.labware
            try:
                command_parsed = Parse(json.dumps(command_params), command())
                commandSequence.append(command_parsed)
            except Exception as e:
                logging.error(f"Error parsing command {command_name} with params {command_params}: {e}")
                raise Exception(f"Error parsing command {command_name} with params {command_params}: {e}")
        self.runSequence(commandSequence)

    def estimateRelease(self, params: Command.Release) -> int:
        return 1

    def estimateEngage(self, params: Command.Engage) -> int:
        return 1

    def estimateUnwind(self, params: Command.Unwind) -> int:
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
