from dataclasses import dataclass
import logging
from enum import Enum
from typing import Optional, List
from tools.pf400.tcp_ip import Pf400TcpIp
from tools.base_server import ABCToolDriver
import time 

class RobotError(Enum):
    """Error codes for the PF400 robot"""
    NO_ROBOT = -1009
    POWER_DISABLED = -1046
    POWER_TIMEOUT = -1025
    NOT_HOMED = -1021
    JOINT_OUT_OF_RANGE = -1012

class Axis(Enum):
    """Robot movement axes"""
    X = "x"
    Y = "y"
    Z = "z"
    YAW = "yaw"
    PITCH = "pitch"
    ROLL = "roll"

@dataclass
class RobotConfig:
    """Configuration for the PF400 robot"""
    tcp_host: str
    tcp_port: int
    grasp_plate_buffer_mm: int = 10
    joints: int = 5
    gpl_version: str = "v1"

@dataclass
class Location:
    """Represents a robot location in either joint or Cartesian space"""
    values: List[float]
    
    def to_string(self) -> str:
        """Convert location to space-separated string"""
        return " ".join(str(round(v, 3)) for v in self.values)
    
    @classmethod
    def from_string(cls, loc_string: str) -> 'Location':
        """Create location from space-separated string"""
        values = [float(x) for x in loc_string.split()]
        return cls(values)

class RobotCommunicator:
    """Handles communication with the robot"""
    def __init__(self, tcp_ip: Pf400TcpIp):
        self.tcp_ip = tcp_ip

    def send_command(self, command: str, expected: Optional[str] = None, 
                    timeout: int = 10) -> str:
        """Send command and get response"""
        if expected:
            self.tcp_ip.write_and_expect(command, expected)
            return expected
        return self.tcp_ip.write_and_read(command, timeout=timeout)

    def wait_for_completion(self) -> None:
        """Wait for end of movement signal"""
        self.tcp_ip.wait_for_eom()

    def get_state(self) -> str:
        return self.tcp_ip.write_and_read("sysState")
    
class RobotState:
    """Manages robot state"""
    def __init__(self) -> None:
        self.is_free: bool = False
        self.gripper_axis_override_value: Optional[float] = None

    @property
    def is_plate_gripped(self) -> bool:
        return self.gripper_axis_override_value is not None

class MovementController:
    """Handles robot movement operations"""
    def __init__(self, communicator: RobotCommunicator, state: RobotState, config:RobotConfig):
        self.communicator = communicator
        self.state = state
        self.config = config 

    def move_joints(self, location: Location, profile_id: int) -> None:
        """Move robot using joint coordinates"""
        loc_values = location.values
        if self.state.gripper_axis_override_value is not None:
            loc_values[4] = self.state.gripper_axis_override_value
        if self.config.joints == 5:
            loc_values = loc_values[:5]
        loc_string = Location(loc_values).to_string()
        if self.config.gpl_version == "v1":
            self.communicator.send_command(f"profidx {profile_id}")
            self.communicator.send_command(f"movej {loc_string}")
        elif self.config.gpl_version == "v2":
            self.communicator.send_command(f"movej {profile_id} {loc_string}")
        self.communicator.wait_for_completion()

    def move_cartesian(self, location: Location, motion_profile: int = 1) -> None:
        """Move robot using Cartesian coordinates"""
        loc_values = location.values
        if self.config.joints == 5:
            loc_values = loc_values[:5]
        loc_string = Location(loc_values).to_string()
        if self.config.gpl_version == "v1":
            self.communicator.send_command(f"movec {loc_string}")
        else:
            self.communicator.send_command(f"movec {motion_profile} {loc_string}")
        self.communicator.wait_for_completion()

    def jog(self, axis: Axis, distance: float) -> None:
        """Jog robot along specified axis"""
        current_loc = self._get_current_cartesian_location()
        new_loc = current_loc.values.copy()

        axis_index = {
            Axis.X: 0, Axis.Y: 1, Axis.Z: 2,
            Axis.YAW: 3, Axis.PITCH: 4, Axis.ROLL: 5
        }[axis]
        
        new_loc[axis_index] += distance
        self.move_cartesian(Location(new_loc))

    def _ensure_not_free(self) -> None:
        """Ensure robot is not in free mode"""
        try:
            self._set_free_mode(-1)
            self.state.is_free = False
        except Exception as e:
            raise RuntimeError(f"Failed to unfree arm: {e}")

    def _get_current_cartesian_location(self) -> Location:
        """Get current Cartesian location"""
        response = self.communicator.send_command("wherec")
        return Location([float(x) for x in response.split()[1:-1]])

    def _get_current_joint_location(self) -> Location:
        """Get current joint location"""
        response = self.communicator.send_command("wherej")
        return Location([float(x) for x in response.split()[1:]])

    def _set_free_mode(self, axis: int, timeout: int = 10) -> None:
        """Set free mode for specified axis"""
        self.communicator.send_command(f"freemode {axis}", timeout=timeout)

class GripperController:
    """Handles gripper operations"""
    def __init__(self, communicator: RobotCommunicator, state: RobotState, config: RobotConfig):
        self.communicator = communicator
        self.state = state
        self.config = config

    def grasp_plate(self, plate_width: int, grip_force: int = 10, speed: int = 10) -> None:
        """Grasp a plate"""
        self.state.gripper_axis_override_value = plate_width - self.config.grasp_plate_buffer_mm
        self.communicator.send_command(
            f"graspplate {plate_width} {speed} {grip_force}",
            expected="0 -1"
        )
        self.communicator.wait_for_completion()

    def release_plate(self, plate_width: int, speed: int = 10) -> None:
        """Release a plate"""
        self.communicator.send_command(f"releaseplate {plate_width} {speed}")
        self.communicator.wait_for_completion()

class RobotInitializer:
    """Handles robot initialization"""
    def __init__(self, communicator: RobotCommunicator, config:RobotConfig ):
        self.communicator = communicator
        self.config = config 

    def initialize(self) -> None:
        """Initialize robot with optimized timeouts"""
        try:
            self._ensure_pc_mode()
            self._ensure_power_on()
            self._ensure_robot_attached()
            self._ensure_robot_homed()
        except Exception as e:
            logging.error(f"Initialization failed: {e}")
            raise

    def _ensure_pc_mode(self) -> None:
        """Ensure robot is in PC mode"""
        response = self.communicator.send_command("mode")
        messages = response.split('\n')

        if len(messages) > 1 or messages[0] != "0 0":
            logging.info("Switching to PC mode...")
            response = self.communicator.send_command("mode 0")
            if response != "0":
                raise Exception(f"Could not switch to PC mode: {response}")
            
            response = self.communicator.send_command("mode")
            if response != "0 0":
                raise Exception(f"Could not verify PC mode: {response}")
            
            logging.info("Switched to PC mode")

    def _ensure_power_on(self, target_states:List[str] =["20", "21"], timeout_seconds:int=40) -> None:
        
        start_time = time.time()
        state = self.communicator.get_state()
        self.communicator.send_command("hp 1")
        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                raise TimeoutError(f"Timed out waiting for system to reach states {target_states}. Current state: {state}")
            
            response = self.communicator.get_state()
            state = response.split(' ')[1]
            if state in target_states:
                return None
            time.sleep(1)

        
    # def _ensure_power_on_v2(self) -> None:
    #     """Ensure robot power is on with shorter timeout"""
    #     response = self.communicator.send_command("hp")
    #     if response != "0 1":
    #         logging.info("Turning on power...")
    #         response = self.communicator.send_command("hp 1 30")
    #         if response != "0":
    #             raise Exception(f"Could not turn power on: {response}")
            
    #         response = self.communicator.send_command("hp")
    #         if response != "0 1":
    #             raise Exception(f"Could not verify power state: {response}")
            
    #         logging.info("Turned power on")
        
    def _ensure_robot_attached(self) -> None:
        """Ensure robot is attached"""
        response = self.communicator.send_command("attach")
        response_splitted = response.split(" ")
        if response_splitted[0] != "0":
            raise Exception(f"Attach failed. Message is {response}")
        if response != "0 1":
            logging.info("Attaching to robot...")
            response = self.communicator.send_command("attach 1")
            if response != "0":
                raise Exception(f"Could not attach to robot: {response}")
            
            response = self.communicator.send_command("attach")
            if response != "0 1":
                raise Exception(f"Could not verify robot attachment: {response}")
            
            logging.info("Attached to robot")


    def _ensure_robot_homed(self) -> None:
        """Ensure robot is homed by first attempting a move and then homing if needed"""
        # Get current joint location from parent class
        current_loc = self.communicator.send_command("wherej")
        current_joint_loc = " ".join(current_loc.split(" ")[1:])
        
        # Try to move to current position to check if homed
        if self.config.gpl_version == "v1":
            message = self.communicator.send_command(f"movej {current_joint_loc}")
        else:
            message = self.communicator.send_command(f"movej 1 {current_joint_loc}")
        # Robot not homed message (-1021)
        if message == "-1021":
            logging.warning("Homing robot...This may take a moment...")
            message = self.communicator.send_command("home", timeout=40)

            if message != "0":
                raise Exception(f"Got malformed message when homing robot. {message}")

            if self.config.gpl_version == "v1":
                message = self.communicator.send_command(f"movej {current_joint_loc}")
            else:
                message = self.communicator.send_command(f"movej 1 {current_joint_loc}")

            if message != "0":
                raise Exception(f"Could not home robot. {message}")

            logging.info("Robot homed")

class Pf400Driver(ABCToolDriver):
    """Main driver class for the PF400 robot"""
    def __init__(self, tcp_host: str, tcp_port: int, joints:int=5, gpl_version:str="v1") -> None:
        self.state = RobotState()
        self.config = RobotConfig(tcp_host=tcp_host, tcp_port=tcp_port, joints=joints, gpl_version=gpl_version)
        self.tcp_ip: Optional[Pf400TcpIp] = None
        self.communicator: Optional[RobotCommunicator] = None 
        self.gripper: Optional[GripperController] = None
        self.initializer: Optional[RobotInitializer] = None
        self.movement: Optional[MovementController] = None
        
    def initialize(self) -> None:
        """Initialize connection to robot"""
        try:
            # Establish new connection
            self.tcp_ip = Pf400TcpIp(self.config.tcp_host, self.config.tcp_port)
            self.communicator = RobotCommunicator(tcp_ip=self.tcp_ip)
            self.gripper = GripperController(
                communicator=self.communicator,
                state=self.state,
                config=self.config
            )
            self.initializer = RobotInitializer(self.communicator, config=self.config)
            
            # Initialize robot state
            if self.initializer is not None:
                self.initializer.initialize()
            self.movement = MovementController(self.communicator, self.state, self.config)
            logging.info("Successfully connected to PF400")
        except Exception as e:
            logging.error(f"Failed to connect to PF400: {str(e)}")
            # Clean up on failure
            if self.tcp_ip is not None:
                try:
                    self.tcp_ip.close()
                except Exception as close_error:
                    logging.warning(f"Error while closing connection during cleanup: {close_error}")
            self.tcp_ip = None
            self.gripper = None
            self.initializer = None
            self.movement = None
            raise

    def close(self) -> None:
        """Close connection to robot"""
        try:
            if hasattr(self, 'tcp_ip') and self.tcp_ip:
                self.tcp_ip.close()
                self.tcp_ip = None
                logging.info("Successfully closed PF400 connection")
        except Exception as e:
            logging.error(f"Error closing PF400 connection: {str(e)}")
            # Still set to None even if close fails
            self.tcp_ip = None

    # Movement commands
    def movej(self, loc_string: str, motion_profile: int = 1) -> None:
        """Move in joint space"""
        if self.movement is None:
            raise RuntimeError("Robot not initialized")
        self.movement.move_joints(Location.from_string(loc_string), motion_profile)

    def movec(self, loc_string: str, motion_profile: int = 1) -> None:
        """Move in Cartesian space"""
        if self.movement is None:
            raise RuntimeError("Robot not initialized")
        self.movement.move_cartesian(Location.from_string(loc_string), motion_profile)

    def jog(self, axis: str, distance: float) -> None:
        """Jog along specified axis"""
        if self.movement is None:
            raise RuntimeError("Robot not initialized")
        try:
            robot_axis = Axis(axis)
            self.movement.jog(robot_axis, distance)
        except ValueError:
            raise Exception(f"Invalid axis {axis}")

    # Free mode commands
    def free(self) -> None:
        """Enable free mode on all axes"""
        if self.movement is None:
            raise RuntimeError("Robot not initialized")
        logging.info("Freeing robot...")
        self.movement._set_free_mode(0, timeout=15)
        self.state.is_free = True

    def safe_free(self) -> None:
        """Enable free mode on all axes except gripper"""
        if self.movement is None:
            raise RuntimeError("Robot not initialized")
        logging.info("Freeing robot, safe mode (exclude gripper axis 5)...")
        for axis in [1, 2, 3, 4, 6]:
            self.movement._set_free_mode(axis, timeout=15)
        self.state.is_free = True

    def unfree(self) -> None:
        """Disable free mode"""
        if self.movement is None:
            raise RuntimeError("Robot not initialized")
        logging.info("Unfreeing robot...")
        self.movement._set_free_mode(-1, timeout=10)
        self.state.is_free = False

    # Gripper commands
    def graspplate(self, plate_width: int, grip_force: int = 10, speed: int = 10) -> None:
        """Grasp a plate"""
        if self.gripper is None:
            raise RuntimeError("Robot not initialized")
        self.gripper.grasp_plate(plate_width, grip_force, speed)

    def releaseplate(self, plate_width: int, speed: int = 10) -> None:
        """Release a plate"""
        if self.gripper is None:
            raise RuntimeError("Robot not initialized")
        self.gripper.release_plate(plate_width, speed)

    def is_plate_gripped(self) -> bool:
        """Check if plate is currently gripped"""
        return self.state.is_plate_gripped

    # Location commands
    def wherej(self) -> str:
        """Get current joint position"""
        if self.communicator is None:
            raise RuntimeError("Robot not initialized")
        return self.communicator.send_command("wherej")

    def set_profile_index(self, profile_index:int ) -> None:
        if self.communicator is None:
            raise RuntimeError("Robot not initialized")
        logging.info(f"Setting profile to index {profile_index}")
        self.communicator.send_command(f"profidx {profile_index}")
        profile_current = self.communicator.send_command("profidx")
        logging.info(f"Profile current {profile_current}")

    def wherec(self) -> str:
        """Get current Cartesian position"""
        if self.communicator is None:
            raise RuntimeError("Robot not initialized")
        return self.communicator.send_command("wherec")

    # Utility commands
    def register_motion_profile(self, profile: str) -> None:
        """Register a motion profile"""
        if self.communicator is None:
            raise RuntimeError("Robot not initialized")
        logging.info(f"Registering motion profile {profile}...")
        self.communicator.send_command(f"profile {profile}")

    def set_sys_speed(self, speed:int) ->  None:
        if self.communicator is None:
            raise RuntimeError("Robot not initialized")
        self.communicator.send_command(f"mspeed {speed}")

    def get_sys_speed(self) -> str:
        if self.communicator is None:
            raise RuntimeError("Robot not initialized")
        return self.communicator.send_command("mspeed")
    
    def halt(self) -> None:
        if self.communicator is None:
            raise RuntimeError("Robot not initialized")
        self.communicator.send_command("halt")
    
    #If the gripper closed fully then no plate was grabbed/detected.
    def gripper_closed_fully(self) -> None:
        if self.communicator is None:
            raise RuntimeError("Robot not initialized")
        self.communicator.send_command("isfullyclosed")

    def home_all(self) -> None:
        if self.communicator is None:
            raise RuntimeError("Robot not initialized")
        self.communicator.send_command("homeAll")

    def home_if_noplate(self) -> None:
        if self.communicator is None:
            raise RuntimeError("Robot not initialized")
        self.communicator.send_command("homall_ifnoplate")

    def move_to_safe(self) -> None:
        if self.communicator is None:
            raise RuntimeError("Robot not initialized")
        self.communicator.send_command("movetosafe")
    
    def set_gripper_open_position(self, width:float) -> None:
        if self.communicator is None:
            raise RuntimeError("Robot not initialized")
        self.communicator.send_command(f"gripopenpos {width}")

    def get_gripper_open_position(self) -> str:
        if self.communicator is None:
            raise RuntimeError("Robot not initialized")
        return self.communicator.send_command("gripopenpos")

    def set_gripper_close_position(self, width:float) -> None:
        if self.communicator is None:
            raise RuntimeError("Robot not initialized")
        self.communicator.send_command(f"gripclosepos {width}")

    def get_gripper_close_position(self) -> str:
        if self.communicator is None:
            raise RuntimeError("Robot not initialized")        
        return self.communicator.send_command("gripclosepos")

    def __del__(self) -> None:
        """Cleanup when driver is destroyed"""
        self.close()

# if __name__ == "__main__":
#     driver = Pf400Driver(
#         tcp_host="192.168.0.1",
#         tcp_port=10100,
#         joints=6,
#         gpl_version="v2"
#     )
#     driver.initialize()

#     logging.info("Getting system speed")
#     driver.get_sys_speed()
#     logging.info("Getting close width")
#     driver.get_gripper_close_position()
#     logging.info("Getting open width")
#     driver.get_gripper_open_position()

