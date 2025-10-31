"""
Direct Bravo hardware control using Python. 
Based off my first attempt at https://github.com/silvioaburto/bravo-py (easier to test with Science Corp hardware!)
"""

import os
import logging
import threading

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


class BravoConnectionError(Exception):
    pass


class BravoCommandError(Exception):
    pass


class BravoDriver:
    def __init__(self, profile: str = None) -> None:
        self.profile = profile
        self._initialized = False
        self.client = None
        
        # Set STA apartment state for ActiveX
        if threading.current_thread() is threading.main_thread():
            # We're in the main thread - need to set apartment state
            try:
                import System
                System.Threading.Thread.CurrentThread.SetApartmentState(
                    System.Threading.ApartmentState.STA
                )
            except Exception as e:
                logging.warning(f"Could not set STA mode: {e}")
                # If that doesn't work, try this
                # try:
                #     import System
                #     System.Threading.Thread.CurrentThread.ApartmentState = (
                #         System.Threading.ApartmentState.STA
                #     )
                # except Exception as e:
                #     logging.warning(f"Could not set STA mode: {e}")
        
        logging.info("Creating Bravo control...")
        try:
            self.client = AxHomewood()
            self.client.CreateControl()
            self.client.Blocking = True
            logging.info("✓ Bravo control created")
        except Exception as e:
            raise BravoConnectionError(f"Failed to create Bravo control: {e}")

    def enumerate_profiles(self) -> list[str]:
        """List available profiles"""
        try:
            profiles = self.client.EnumerateProfiles()
            logging.info(f"Available profiles: {profiles}")
            return profiles
        except Exception as e:
            logging.error(f"Failed to enumerate profiles: {e}")
            return []

    def get_activex_version(self) -> str:
        """Get ActiveX version"""
        try:
            return self.client.GetActiveXVersion()
        except Exception as e:
            return f"Error: {e}"

    def show_diagnostics(self) -> str:
        """Show diagnostics dialog"""
        try:
            return self.client.ShowDiagsDialog(True,1)
        except Exception as e:
            return f"Error: {e}"
    
    def get_firmware_version(self) -> str:
        """Get firmware version"""
        try:
            return self.client.GetFirmwareVersion()
        except Exception as e:
            return f"Error: {e}"
    
    def get_hardware_version(self) -> str:
        """Get hardware version"""
        try:
            return self.client.GetHardwareVersion()
        except Exception as e:
            return f"Error: {e}"
    
    def initialize(self, profile:str=None) -> bool:
        """Initialize with a profile"""
        if profile:
            self.profile = profile
        
        if not self.profile:
            raise ValueError("Profile name required")
        
        try:
            logging.info(f"Initializing with profile: {self.profile}")
            result = self.client.Initialize(self.profile)
            
            if result == 0:
                self._initialized = True
                logging.info("✓ Bravo initialized successfully")
                return True
            else:
                error = self.get_last_error()
                logging.error(f"Initialize failed with code {result}: {error}")
                return False
        except Exception as e:
            error = self.get_last_error()
            raise BravoCommandError(f"Initialize failed: {e}\nDevice error: {error}")
    
    def close(self) -> bool:
        """Close the connection"""
        if not self._initialized:
            return True
        
        try:
            self.client.Close()
            self._initialized = False
            logging.info("✓ Bravo closed")
            return True
        except Exception as e:
            logging.error(f"Failed to close: {e}")
            return False

    def home_xyz(self) -> bool:
        """Home X, Y, Z axes"""
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        
        try:
            self.client.HomeXYZ()
            logging.info("✓ HomeXYZ complete")
            return True
        except Exception as e:
            error = self.get_last_error()
            raise BravoCommandError(f"HomeXYZ failed: {e}\nDevice error: {error}")
    
    def aspirate(self, volume : float, plate_location : int,
                 distance_from_well_bottom: float = 0.0,
                 pre_aspirate_volume: float = 0.0,
                 post_aspirate_volume: float = 0.0,
                 retract_distance_per_microliter: float = 0.0) -> bool:
        """Aspirate liquid"""
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        
        try:
            self.client.Aspirate(
                volume,
                pre_aspirate_volume,
                post_aspirate_volume,
                plate_location,
                distance_from_well_bottom,
                retract_distance_per_microliter
            )
            logging.info(f"✓ Aspirated {volume}µL from location {plate_location}")
        except Exception as e:
            error = self.get_last_error()
            raise BravoCommandError(f"Aspirate failed: {e}\nDevice error: {error}")
    
    def dispense(self, volume: float, empty_tips: bool, blow_out_volume: float,
                 plate_location: int, distance_from_well_bottom: float = 0.0,
                 retract_distance_per_microliter: float = 0.0) -> bool:
        """Dispense liquid"""
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        
        try:
            self.client.Dispense(
                volume,
                empty_tips,
                blow_out_volume,
                plate_location,
                distance_from_well_bottom,
                retract_distance_per_microliter
            )
            logging.info(f"✓ Dispensed {volume}µL to location {plate_location}")
        except Exception as e:
            error = self.get_last_error()
            raise BravoCommandError(f"Dispense failed: {e}\nDevice error: {error}")
    
    def tips_on(self, plate_location: int) -> bool:
        """Pick up tips"""
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        
        try:
            self.client.TipsOn(plate_location)
            logging.info(f"✓ Tips on at location {plate_location}")
            return True
        except Exception as e:
            error = self.get_last_error()
            raise BravoCommandError(f"TipsOn failed: {e}\nDevice error: {error}")
    
    def tips_off(self, plate_location: int) -> bool:
        """Eject tips"""
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        
        try:
            self.client.TipsOff(plate_location)
            logging.info(f"✓ Tips off at location {plate_location}")
            return True
        except Exception as e:
            error = self.get_last_error()
            raise BravoCommandError(f"TipsOff failed: {e}\nDevice error: {error}")
    
    def move_to_location(self, plate_location: int, only_z: bool = False) -> bool:
        """Move to location"""
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        
        try:
            self.client.MoveToLocation(plate_location, only_z)
            logging.info(f"✓ Moved to location {plate_location}")
            return True
        except Exception as e:
            error = self.get_last_error()
            raise BravoCommandError(f"Move failed: {e}\nDevice error: {error}")
    
    def set_labware_at_location(self, plate_location: int, labware_type: str) -> bool:
        """Set labware at location"""
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        
        try:
            self.client.SetLabwareAtLocation(plate_location, labware_type)
            logging.info(f"✓ Set labware '{labware_type}' at location {plate_location}")
            return True
        except Exception as e:
            error = self.get_last_error()
            raise BravoCommandError(f"SetLabware failed: {e}\nDevice error: {error}")
    
    def set_liquid_class(self, liquid_class: str) -> bool:
        """Set liquid class"""
        if not self._initialized:
            raise BravoCommandError("Not initialized")
        
        try:
            self.client.SetLiquidClass(liquid_class)
            logging.info(f"✓ Set liquid class '{liquid_class}'")
            return True
        except Exception as e:
            error = self.get_last_error()
            raise BravoCommandError(f"SetLiquidClass failed: {e}\nDevice error: {error}")

    def get_last_error(self) -> str:
        """Get last error"""
        try:
            return self.client.GetLastError()
        except Exception as e:
            logging.error(f"Error retrieving last error: {e}")
            return "Could not retrieve error"
    
    # def __enter__(self):
    #     """Context manager entry"""
    #     if self.profile and not self._initialized:
    #         self.initialize()
    #     return self
    
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     """Context manager exit"""
    #     self.close()
    
    def __del__(self) -> None:
        """Cleanup"""
        try:
            if self._initialized:
                self.close()
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")


# Test script
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("BRAVO DRIVER TEST")
    print("=" * 60)
    
    try:
        # Create driver
        bravo = BravoDriver()
        
        # Get versions
        print(f"\nActiveX Version: {bravo.get_activex_version()}")
        print(f"Firmware Version: {bravo.get_firmware_version()}")
        print(f"Hardware Version: {bravo.get_hardware_version()}")
        
        bravo.initialize("Mol Bio Bravo")
        

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()