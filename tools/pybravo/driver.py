"""
Direct Bravo hardware control using Python. 
Based off my first attempt at https://github.com/silvioaburto/bravo-py (easier to test with Science Corp hardware!)
"""

import os
import logging
import threading
from functools import wraps
from typing import Callable, Any, Optional, cast

if os.name == "nt":
    import clr # type: ignore

    SDK_DLL = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "DLLs",
        "AxInterop.HomewoodLib.dll",
    )

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


class BravoDriver:
    def __init__(self, profile: Optional[str] = None) -> None:
        self.profile = profile
        self._initialized = False
        self.client: Optional[Any] = None
        
        # Set STA apartment state for ActiveX
        if threading.current_thread() is threading.main_thread():
            # We're in the main thread - need to set apartment state
            import System  # type: ignore
            System.Threading.Thread.CurrentThread.SetApartmentState(
                System.Threading.ApartmentState.STA
            )

        logging.info("Creating Bravo control...")
        self.client = AxHomewood()
        self.client.CreateControl()
        self.client.Blocking = True
        logging.info("✓ Bravo control created")


    def enumerate_profiles(self) -> list[str]:
        """List available profiles"""
        if self.client is None:
            return []
        profiles_net = self.client.EnumerateProfiles()
        profiles = list(profiles_net) if profiles_net else []
        logging.info(f"Available profiles: {profiles}")
        return profiles

    def get_device_configuration(self) -> str:
        """Get device configuration"""
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


    def show_diagnostics(self) -> int:
        """Show diagnostics dialog"""
        if self.client is None:
            raise BravoCommandError("Client not initialized")
        return cast(int, self.client.ShowDiagsDialog(True, 1))

    def get_firmware_version(self) -> str:
        """Get firmware version"""
        if self.client is None:
            raise BravoCommandError("Client not initialized")
        result = self.client.GetFirmwareVersion()
        return str(result)
    
    @check_bravo_result
    def initialize(self, profile: Optional[str] = None) -> int:
        """Initialize with a profile"""
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

    def close(self) -> bool:
        """Close the connection"""
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

    @check_bravo_result
    def home_w(self) -> int:
        if not self._initialized:
            raise BravoCommandError("Bravo not initialized")
        if self.client is None:
            raise BravoCommandError("Client not initialized")
        logging.info("Homing W axis...")
        result = self.client.HomeW()
        logging.info("✓ HomeW complete")
        return cast(int, result)
    
    @check_bravo_result
    def home_xyz(self) -> int:
        """Home X, Y, Z axes"""
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        if self.client is None:
            raise BravoCommandError("Client not initialized")
        result = self.client.HomeXYZ()
        logging.info("✓ HomeXYZ complete")
        return cast(int, result)
    
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
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        if self.client is None:
            raise BravoCommandError("Client not initialized")
        logging.info(f"Mixing {cycles} cycles of {volume}µL at location {plate_location}...")
        result = self.client.Mix(volume, pre_aspirate_volume, blow_out_volume, cycles, plate_location, distance_from_well_bottom, retract_distance_per_microliter)
        logging.info("✓ Mix complete")
        return cast(int, result)
    
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


    @check_bravo_result
    def aspirate(self, volume: float, plate_location: int,
                 distance_from_well_bottom: float = 0.0,
                 pre_aspirate_volume: float = 0.0,
                 post_aspirate_volume: float = 0.0,
                 retract_distance_per_microliter: float = 0.0) -> int:
        """Aspirate liquid"""
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
    
    @check_bravo_result
    def dispense(self, volume: float, empty_tips: bool, blow_out_volume: float,
                 plate_location: int, distance_from_well_bottom: float = 0.0,
                 retract_distance_per_microliter: float = 0.0) -> int:
        """Dispense liquid"""
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

    @check_bravo_result
    def tips_on(self, plate_location: int) -> int:
        """Pick up tips"""
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        if self.client is None:
            raise BravoCommandError("Client not initialized")
        logging.info(f"Picking up tips at location {plate_location}...")
        result = self.client.TipsOn(plate_location)
        logging.info(f"✓ Tips on at location {plate_location}")
        return cast(int, result)
    
    @check_bravo_result
    def tips_off(self, plate_location: int) -> int:
        """Eject tips"""
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        if self.client is None:
            raise BravoCommandError("Client not initialized")
        logging.info(f"Ejecting tips at location {plate_location}...")
        result = self.client.TipsOff(plate_location)
        logging.info(f"✓ Tips off at location {plate_location}")
        return cast(int, result)

    @check_bravo_result
    def move_to_location(self, plate_location: int, only_z: bool = False) -> int:
        """Move head to location"""
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        
        if self.client is None:
            raise BravoCommandError("Client not initialized")
        
        result = self.client.MoveToLocation(plate_location, only_z)
        logging.info(f"✓ Moved to location {plate_location}")
        return cast(int, result)

    
    @check_bravo_result
    def set_labware_at_location(self, plate_location: int, labware_type: str) -> int:
        """Set labware at location"""
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        
        if self.client is None:
            raise BravoCommandError("Client not initialized")
        
        result = self.client.SetLabwareAtLocation(plate_location, labware_type)
        logging.info(f"✓ Set labware '{labware_type}' at location {plate_location}")
        return cast(int, result)
 
    @check_bravo_result
    def set_liquid_class(self, liquid_class: str) -> int:
        """Set liquid class"""
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        
        if self.client is None:
            raise BravoCommandError("Client not initialized")
        
        result = self.client.SetLiquidClass(liquid_class)
        logging.info(f"✓ Set liquid class '{liquid_class}'")
        return cast(int, result)

    @check_bravo_result
    def pick_and_place(self, source_location: int, dest_location: int, gripper_offset: float, labware_thickness: float) -> int:
        """Picks a plate from start location and places at end locaiton using gripper offset"""
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        
        if self.client is None:
            raise BravoCommandError("Client not initialized")
        
        logging.info(f"Picking plate from location {source_location} and placing at location {dest_location}...")
        result = self.client.PickAndPlace(source_location, dest_location, gripper_offset, labware_thickness)
        logging.info("✓ Pick and place complete")
        return cast(int, result)

    def get_last_error(self) -> str:
        """Get last error"""
        try:
            if self.client is None:
                return "Client not initialized"
            result = self.client.GetLastError()
            return str(result)
        except Exception as e:
            logging.error(f"Error retrieving last error: {e}")
            return "Could not retrieve error"

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
        with BravoDriver() as bravo:
            bravo.initialize("Mol Bio Bravo")
            logging.info(bravo.get_device_configuration())
            logging.info(f"Firmware Version: {bravo.get_firmware_version()}")
            # bravo.home_w()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()