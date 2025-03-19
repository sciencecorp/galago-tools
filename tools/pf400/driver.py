from dataclasses import dataclass
import logging
import time
from enum import Enum
from typing import Optional, List
from tools.pf400.tcp_ip import Pf400TcpIp
from tools.base_server import ABCToolDriver

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
    def __init__(self, communicator: RobotCommunicator, state: RobotState):
        self.communicator = communicator
        self.state = state

    def move_joints(self, location: Location, motion_profile: int = 1) -> None:
        """Move robot using joint coordinates"""
        if self.state.is_free:
            self._ensure_not_free()

        loc_values = location.values
        if self.state.gripper_axis_override_value is not None:
            loc_values[4] = self.state.gripper_axis_override_value
        
        loc_string = Location(loc_values).to_string()
        self.communicator.send_command(f"movej {motion_profile} {loc_string}")
        self.communicator.wait_for_completion()

    def move_cartesian(self, location: Location, motion_profile: int = 1) -> None:
        """Move robot using Cartesian coordinates"""
        if self.state.is_free:
            self._ensure_not_free()
            
        self.communicator.send_command(f"movec {motion_profile} {location.to_string()}")
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
            logging.error(f"Failed to unfree arm: {e}")
            raise

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
        self.state.gripper_axis_override_value = None
        self.communicator.send_command(f"releaseplate {plate_width} {speed}")
        self.communicator.wait_for_completion()

class RobotInitializer:
    """Handles robot initialization"""
    def __init__(self, communicator: RobotCommunicator):
        self.communicator = communicator

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

    def _ensure_power_on(self) -> None:
        message = self.communicator.send_command("hp")
        tokens = message.split(" ")
        if tokens[0] != "0":
            raise Exception(f"Got malformed message when requesting power state. {message}")
        if tokens[1] != "1":
            # Wait 10 seconds for power to come on.
            logging.info("Turning on power...")
            message = self.communicator.write_and_read("hp 1 30")
            if message != "0":
                raise Exception(f"Could not turn power on. {message}")
            message = self.communicator.write_and_read("hp")
            if message != "0 1":
                raise Exception(f"Could not turn power on. {message}")

            logging.info("Turned power on")
    # def ensure_power_on(self) -> None:
    #     message = self.communicator.send_command("hp")
    #     tokens = message.split(" ")
        
    #     # Check for malformed message
    #     if not tokens or tokens[0] != "0":
    #         raise Exception(f"Got malformed message when requesting power state. {message}")
        
    #     # Check if power is already on (tokens should be ["0", "1"])
    #     if len(tokens) > 1 and tokens[1] == "1":
    #         # Power is already on, nothing to do
    #         return
        
    #     # Power is off or status format unexpected, try to turn power on
    #     logging.info("Turning on power...")
    #     message = self.communicator.write_and_read("hp 1")
    #     if message != "0":
    #         raise Exception(f"Could not turn power on. {message}")
        
    #     # Verify power is now on
    #     message = self.communicator.write_and_read("hp")
    #     if message != "0 1":
    #         raise Exception(f"Could not turn power on. {message}")
        
    #     logging.info("Turned power on")

    def _ensure_robot_attached(self) -> None:
        """Ensure robot is attached"""
        response = self.communicator.send_command("attach")
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
        message = self.communicator.send_command(f"movej 1 {current_joint_loc}")

        # Robot not homed message (-1021)
        if message == "-1021":
            logging.info("Homing robot...This may take a moment...")
            message = self.communicator.send_command("home", timeout=30)

            if message != "0":
                raise Exception(f"Got malformed message when homing robot. {message}")

            # Try move again after homing
            message = self.communicator.send_command(f"movej 1 {current_joint_loc}")

            if message != "0":
                raise Exception(f"Could not home robot. {message}")

            logging.info("Robot homed")

class Pf400Driver(ABCToolDriver):
    """Main driver class for the PF400 robot"""
    def __init__(self, tcp_host: str, tcp_port: int) -> None:
        self.state = RobotState()
        self.config = RobotConfig(tcp_host=tcp_host, tcp_port=tcp_port)
        # Initialize with Optional types
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
            self.initializer = RobotInitializer(self.communicator)
            
            # Initialize robot state
            if self.initializer is not None:
                self.initializer.initialize()
            self.movement = MovementController(self.communicator, self.state)
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
            self.communicator = None
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

    def wait(self, duration: int) -> None:
        """Wait for specified duration"""
        time.sleep(duration)

    def __del__(self) -> None:
        """Cleanup when driver is destroyed"""
        self.close()