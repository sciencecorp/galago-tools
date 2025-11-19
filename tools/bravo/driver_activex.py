"""
Direct Bravo hardware control using Python. 


*** For future reference *** 
Turns out that Agilent only made some of the Bravo SDK available via ActiveX, despite an activex object available. 
(python -m win32com.client.makepy)
methods like home, tips on, tips off DO NOT work properly via COM. And SetLabwareAtLocation
fails with no obvious exception. Others such as Initialize and MoveTolocation work fine. There are some workarounds to some of these such as setting labware,
via diagnostics dialog, but this requires manual intervention. The same behavior is observed 
when using an ActiveX Object via a vworks protocol which sort of proves this is not necessarily a dependency issue. 

I've attempted multiple ways to get around this including using pywin32, comtypes, and directly via clr with no success. Therefore, 
we can only assume it is not possible to fully control the Bravo via COM/ActiveX as Agilent has not exposed the full functionality and there are some
vworks native calls that are not possible to replicate.

#Example VwOrks snippet that uses ActiveX object
var ocx
if( ocx == undefined){
ocx = new ActiveX( "HW.HomewoodCtrl.1");
}

for( x in ocx.members)
print( x)



ocx.set("Blocking", true);  // Use set() method to set the Blocking property
print("Initializing Bravo!")
var result = ocx.Initialize("Mol Bio Bravo");
if (result != 0) {
    var error = ocx.GetLastError();
    throw new Error("Initialize failed: " + error);
}
print("Bravo initalized!")

"""

import os
import logging
import threading
from functools import wraps
from typing import Callable, Any, Optional, cast
from tools.base_server import ABCToolDriver
from tools.bravo.registry import BravoRegistry
import queue

if os.name == "nt":
    import clr # type: ignore

    SDK_DLL = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "DLLs",
        "AxInterop.HomewoodLib.dll",
    )

    BRAVO_WRAPPER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "DLLs",
        "BravoShim.dll",
    )
    clr.AddReference(BRAVO_WRAPPER)
    import BravoShim  # type: ignore

    if not os.path.exists(SDK_DLL):
        raise FileNotFoundError(f"Bravo SDK DLL not found at {SDK_DLL}")

    clr.AddReference(SDK_DLL)
    from AxHomewoodLib import AxHomewood  # type: ignore


def check_bravo_result(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to check error after call.
    """
    @wraps(func)
    def wrapper(self: 'BravoDriver', *args: Any, **kwargs: Any) -> Any:
        result = func(self, *args, **kwargs)
        
        # Check if result is an integer and not 0 (success)
        if isinstance(result, int) and result != 0:
            error = self.get_last_error()
            raise BravoCommandError(
                f"{func.__name__} failed with code {result}: {error}"
            )
        
        return result
    return wrapper


class BravoConnectionError(Exception):
    pass


class BravoCommandError(Exception):
    pass


class STAThread:
    """Dedicated STA thread for ActiveX control operations"""
    def __init__(self) -> None:
        self.command_queue: queue.Queue[Any] = queue.Queue()
        self.result_queue: queue.Queue[Any] = queue.Queue()
        self.thread: Optional[threading.Thread] = None
        self.running = False
        
    def start(self) -> None:
        """Start the STA thread"""
        self.running = True
        self.thread = threading.Thread(target=self._run_sta_thread, daemon=True)
        self.thread.start()
        
    def stop(self) -> None:
        """Stop the STA thread"""
        self.running = False
        self.command_queue.put(None)
        if self.thread:
            self.thread.join(timeout=5.0)
    
    def _run_sta_thread(self) -> None:
        """Run loop for STA thread"""
        import System  # type: ignore
        System.Threading.Thread.CurrentThread.SetApartmentState(
            System.Threading.ApartmentState.STA
        )
        
        logging.info("STA thread started for Bravo ActiveX control")
        
        while self.running:
            try:
                command = self.command_queue.get(timeout=1.0)
                if command is None:
                    break
                    
                func, args, kwargs = command
                try:
                    result = func(*args, **kwargs)
                    self.result_queue.put(('success', result))
                except Exception as e:
                    self.result_queue.put(('error', e))
                    
            except queue.Empty:
                continue
        
        logging.info("STA thread stopped")
    
    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute a function on the STA thread and wait for result"""
        self.command_queue.put((func, args, kwargs))
        status, result = self.result_queue.get()
        
        if status == 'error':
            raise result
        return result


class BravoDriver(ABCToolDriver):
    def __init__(self, profile: Optional[str] = None) -> None:
        self.profile = profile
        self._initialized = False
        self.client: Optional[Any] = None
        self.sta_thread = STAThread()
        
        # Start dedicated STA thread
        self.sta_thread.start()
        self.registry: BravoRegistry = BravoRegistry(profile_name=profile or "")
        
        # Create control on STA thread
        logging.info("Creating Bravo control...")
        self.sta_thread.execute(self._create_control)
        logging.info("✓ Bravo control created")

    def _create_control(self) -> None:
        """Create ActiveX control - must run on STA thread"""
        self.client = AxHomewood()
        self.client.CreateControl()
        
        # Ensure blocking mode is actually set
        self.client.Blocking = True
        current_blocking = self.client.Blocking
        logging.info(f"Blocking mode set to: {current_blocking}")
        
        if not current_blocking:
            logging.error("WARNING: Blocking mode failed to set!")

    
    def enumerate_profiles(self) -> list[str]:
        """List available profiles"""
        def _enumerate() -> list[str]:
            if self.client is None:
                return []
            profiles_net = self.client.EnumerateProfiles()
            profiles: list[str] = list(profiles_net) if profiles_net else []
            logging.info(f"Available profiles: {profiles}")
            return profiles
        
        result: list[str] = self.sta_thread.execute(_enumerate)
        return result

    def get_device_configuration(self) -> str:
        """Get device configuration"""
        def _get_config() -> str:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            
            result = self.client.GetDeviceConfiguration("")
            
            error_code, config = result
            if error_code != 0:
                error = self.get_last_error()
                raise BravoCommandError(f"GetDeviceConfiguration failed with code {error_code}: {error}")
            return str(config) if config else ""
        
        result: str = self.sta_thread.execute(_get_config)
        return result
    
    
    
    def initialize_axis(self, axis: str, initialize_if_homed: bool) -> int:
        """Initialize a specific axis"""
        def _initialize_axis() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            logging.info(f"Initializing axis {axis}...")
            result = self.client.Initializeaxis(axis, initialize_if_homed)
            logging.info(f"✓ Axis {axis} initialized")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_initialize_axis)
        return result
    
    def show_diagnostics(self) -> int:
        """Show diagnostics dialog"""
        def _show_diags() -> int:
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            return cast(int, self.client.ShowDiagsDialog(True, 1))
        
        result: int = self.sta_thread.execute(_show_diags)
        return result

    def get_firmware_version(self) -> str:
        """Get firmware version"""
        def _get_version() -> str:
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            result = self.client.GetFirmwareVersion()
            return str(result)
        
        result: str = self.sta_thread.execute(_get_version)
        return result
    
    @check_bravo_result
    def initialize(self, profile: Optional[str] = None) -> int:
        """Initialize with a profile"""
        def _initialize() -> int:
            if profile:
                self.profile = profile
            
            if not self.profile:
                raise ValueError("Profile name required")
            
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            
            logging.info(f"Initializing with profile: {self.profile}")
            result = self.client.Initialize(self.profile)
            if result == 0:
                self._initialized = True
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_initialize)
        return result

    def close(self) -> bool:
        """Close the connection"""
        def _close() -> bool:
            if not self._initialized:
                return True
            
            if self.client is None:
                return True
            
            try:
                self.client.Close()
                self._initialized = False
                logging.info("✓ Bravo closed")
                return True
            except Exception as e:
                raise BravoCommandError(f"Close failed: {e}")
        
        result: bool = self.sta_thread.execute(_close)
        self.sta_thread.stop()
        return result

    @check_bravo_result
    def home_w(self) -> int:
        def _home_w() -> int:
            if not self._initialized:
                raise BravoCommandError("Bravo not initialized")
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            logging.info("Homing W axis...")
            result = self.client.HomeW()
            logging.info("✓ HomeW complete")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_home_w)
        return result
    
    @check_bravo_result
    def enable_y(self) -> int:
        """Enable Y axis"""
        def _enable_y() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            logging.info("Enabling Y axis...")
            result = self.client.EnableY()
            logging.info("✓ EnableY complete")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_enable_y)
        return result
    
    @check_bravo_result
    def home_xyz(self) -> int:
        """Home X, Y, Z axes"""
        def _home_xyz() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            result = self.client.HomeXYZ()
            logging.info("✓ HomeXYZ complete")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_home_xyz)
        return result
    
    @check_bravo_result
    def mix(self, 
            volume: float, 
            pre_aspirate_volume: float, 
            blow_out_volume: float, 
            cycles: int, 
            plate_location: int,
            distance_from_well_bottom: float, 
            retract_distance_per_microliter: float
            ) -> int:
        """Mix liquid"""
        def _mix() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            logging.info(f"Mixing {cycles} cycles of {volume}µL at location {plate_location}...")
            result = self.client.Mix(volume, pre_aspirate_volume, blow_out_volume, cycles, plate_location, distance_from_well_bottom, retract_distance_per_microliter)
            logging.info("✓ Mix complete")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_mix)
        return result
    
    @check_bravo_result
    def wash(self, 
             volume: float,
             empty_tips: bool,
             pre_aspirate_volume: float,
             blow_out_volume: float,
             cycles: int, 
             plate_location: int,
             distance_from_well_bottom: float,
             retract_distance_per_microliter: float,
             pump_in_flow_speed: float,
             pump_out_flow_speed: float
             ) -> int:
        """Wash tips"""
        def _wash() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            logging.info(f"Washing tips with {cycles} cycles of {volume}µL at location {plate_location}...")
            result = self.client.Wash(
                volume,
                empty_tips,
                pre_aspirate_volume,
                blow_out_volume,
                cycles,
                plate_location,
                distance_from_well_bottom,
                retract_distance_per_microliter,
                pump_in_flow_speed,
                pump_out_flow_speed
            )
            logging.info("✓ Wash complete")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_wash)
        return result

    @check_bravo_result
    def aspirate(self, volume: float, plate_location: int,
                 distance_from_well_bottom: float = 0.0,
                 pre_aspirate_volume: float = 0.0,
                 post_aspirate_volume: float = 0.0,
                 retract_distance_per_microliter: float = 0.0) -> int:
        """Aspirate liquid"""
        def _aspirate() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            
            try:
                result = self.client.Aspirate(
                    volume,
                    pre_aspirate_volume,
                    post_aspirate_volume,
                    plate_location,
                    distance_from_well_bottom,
                    retract_distance_per_microliter
                )
                logging.info(f"✓ Aspirated {volume}µL from location {plate_location}")
                return cast(int, result)
            except Exception as e:
                error = self.get_last_error()
                raise BravoCommandError(f"Aspirate failed: {e}\nDevice error: {error}")
        
        result: int = self.sta_thread.execute(_aspirate)
        return result
    
    @check_bravo_result
    def dispense(self, volume: float, empty_tips: bool, blow_out_volume: float,
                 plate_location: int, distance_from_well_bottom: float = 0.0,
                 retract_distance_per_microliter: float = 0.0) -> int:
        """Dispense liquid"""
        def _dispense() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            
            logging.info(f"Dispensing {volume}µL to location {plate_location}...")
            result = self.client.Dispense(
                volume,
                empty_tips,
                blow_out_volume,
                plate_location,
                distance_from_well_bottom,
                retract_distance_per_microliter
            )
            logging.info(f"✓ Dispensed {volume}µL to location {plate_location}")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_dispense)
        return result

    @check_bravo_result
    def tips_on(self, plate_location: int) -> int:
        """Pick up tips"""
        def _tips_on() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            logging.info(f"Picking up tips at location {plate_location}...")
            result = self.client.TipsOn(plate_location)
            logging.info(f"✓ Tips on at location {plate_location}")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_tips_on)
        return result
    
    @check_bravo_result
    def tips_off(self, plate_location: int) -> int:
        """Eject tips"""
        def _tips_off() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            logging.info(f"Ejecting tips at location {plate_location}...")
            result = self.client.TipsOff(plate_location)
            logging.info(f"✓ Tips off at location {plate_location}")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_tips_off)
        return result
    
    @check_bravo_result
    def move_to_position(self, axis: int, position: float, velocity: float, acceleration: float) -> int:
        """Move head to position"""
        def _move() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            
            w_props = self.registry.fetch_axis_properties('W')
            w_offset = w_props.homing_offset if w_props else 0.0
            w_acc = w_props.homing_acceleration if w_props else 0.0
            w_vel = w_props.homing_velocity if w_props else 0.0
            logging.info(f"Moving axis {axis} to position {w_offset} (vel: {w_vel}, acc: {w_acc})...")
            result = self.client.MoveToPosition(axis, w_offset, w_vel, w_acc)
            logging.info(f"Result of move: {result}")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_move)
        return result
    
    @check_bravo_result
    def move_to_location(self, plate_location: int, only_z: bool = False) -> int:
        """Move head to location"""
        def _move_to_loc() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            
            result = self.client.MoveToLocation(plate_location, only_z)
            logging.info(f"✓ Moved to location {plate_location}")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_move_to_loc)
        return result
    
    def set_labware_at_location(self, plate_location: int, labware_type: str) -> int:
        """Set labware at location"""
        def _set_labware() -> int:
            # if not self._initialized:
            #     raise BravoCommandError("Not initialized")
            
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            
            logging.info(f"Setting labware '{labware_type}' at location {plate_location}...")
            result = self.client.SetLabwareAtLocation(plate_location, labware_type)
            logging.info(f"Result of set labware: {result}")
            logging.info(f"✓ Labware '{labware_type}' set at location {plate_location}")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_set_labware)
        return result


    def set_head_mode(self, head_mode: int) -> int:
        """Set head mode"""
        def _set_head_mode() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            
            logging.info(f"Setting head mode to {head_mode}...")
            result = self.client.SetHeadMode(head_mode)
            logging.info(f"✓ Head mode set to {head_mode}")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_set_head_mode)
        return result

    def get_labware_at_location(self, plate_location: int) -> tuple[int, str]:
        """Get labware at location"""
        def _get_labware() -> tuple[int, str]:
            if self.client is None:
                raise BravoCommandError("Client not initialized")

            code, name = BravoShim.Wrapper.GetLabware(self.client, plate_location)

            logging.info(f"✓ Labware at location {plate_location}: '{name}' (code {code})")
            return cast(int, code), str(name)
        
        result: tuple[int, str] = self.sta_thread.execute(_get_labware)
        return result
        
    @check_bravo_result
    def set_liquid_class(self, liquid_class: str) -> int:
        """Set liquid class"""
        def _set_liquid() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            
            result = self.client.SetLiquidClass(liquid_class)
            logging.info(f"✓ Set liquid class '{liquid_class}'")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_set_liquid)
        return result

    @check_bravo_result
    def pick_and_place(self, source_location: int, dest_location: int, gripper_offset: float, labware_thickness: float) -> int:
        """Picks a plate from start location and places at end location using gripper offset"""
        def _pick_and_place() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            
            logging.info(f"Picking plate from location {source_location} and placing at location {dest_location}...")
            result = self.client.PickAndPlace(source_location, dest_location, gripper_offset, labware_thickness)
            logging.info("✓ Pick and place complete")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_pick_and_place)
        return result

    def disable_motors(self) -> int:
        """Disable motors"""
        def _disable_motors() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            logging.info("Disabling motors...")
            result = self.client.DisableMotors()
            logging.info("✓ Motors disabled")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_disable_motors)
        return result
        
    def enable_motors(self) -> int:
        """Enable motors"""
        def _enable_motors() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            logging.info("Enabling motors...")
            result = self.client.EnableXYZ()
            logging.info("✓ Motors enabled")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_enable_motors)
        return result
    
    def enable_x_axis(self) -> int:
        """Enable X axis"""
        def _enable_x() -> int:
            if not self._initialized:
                raise BravoCommandError("Not initialized")
            if self.client is None:
                raise BravoCommandError("Client not initialized")
            logging.info("Enabling X axis...")
            result = self.client.EnableXAxis()
            logging.info("✓ X axis enabled")
            return cast(int, result)
        
        result: int = self.sta_thread.execute(_enable_x)
        return result
        
    def get_last_error(self) -> str:
        """Get last error"""
        def _get_error() -> str:
            try:
                if self.client is None:
                    return "Client not initialized"
                result = self.client.GetLastError()
                return str(result)
            except Exception as e:
                logging.error(f"Error retrieving last error: {e}")
                return "Could not retrieve error"
        
        result: str = self.sta_thread.execute(_get_error)
        return result

    def __enter__(self) -> 'BravoDriver':
        """Context manager entry"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit"""
        self.close()
    

# Test script
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("BRAVO DRIVER TEST")
    print("=" * 60)
    try:
        # Create driver
        with BravoDriver("Mol Bio Bravo") as bravo:
            bravo.initialize("Mol Bio Bravo")
            # err, name = bravo.get_labware_at_location(5)

            # config = bravo.get_device_configuration()
            # logging.info(f"Device Configuration: {config}")
            bravo.set_head_mode(1)  # Set to 96-channel mode
            # # #Set labware to position 5
            # bravo.set_labware_at_location(2, "96 V11 LT250 Tip Box Standard")
            # # bravo.set_labware_at_location(6, "96 V11 LT250 Tip Box Standard")
            # bravo.move_to_location(1)
            # bravo.show_diagnostics()
            # bravo.tips_on(2)
            # bravo.tips_off(2)
            bravo.show_diagnostics()
            # logging.info("Made it here")
            # #Check the locations 
            # logging.info(f"Location 5: Error {err}, Labware '{name}'")
            # bravo.get_labware_at_location(6)
            # bravo.get_labware_at_location(7)
        # #Pick up tips
        # bravo.tips_on(5)

        # #Drop off tips at location 6 

        # bravo.tips_off(5)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()