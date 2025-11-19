import logging
from typing import TYPE_CHECKING, Dict, Any, Optional
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

# Import winreg only on Windows, but always make it available for type checking
if TYPE_CHECKING:
    import winreg
elif os.name == "nt":
    import winreg


@dataclass
class AxisProperties:
    """Properties for a Bravo axis"""
    homing_offset: float
    homing_acceleration: float
    homing_velocity: float
    
    @classmethod
    def from_registry_data(cls, data: Dict[str, Any]) -> 'AxisProperties':
        """Create AxisProperties from registry data"""
        return cls(
            homing_offset=float(data.get('Homing offset', 0.0)),
            homing_acceleration=float(data.get('Homing acceleration', 0.0)),
            homing_velocity=float(data.get('Homing velocity', 0.0)),
        )


class BravoRegistry:
    """Handler for Bravo profile registry operations"""
    
    BASE_PATH = r"SOFTWARE\WOW6432Node\Velocity11\Bravo2\Profiles"
    
    def __init__(self, profile_name: str):
        """
        Initialize BravoRegistry with a specific profile
        
        Args:
            profile_name: Name of the Bravo profile (default: "Mol Bio Bravo")
        """
        if os.name != "nt":
            raise RuntimeError("Bravo registry access is only supported on Windows systems.")
        self.profile_name = profile_name
        self.profile_path = f"{self.BASE_PATH}\\{profile_name}"
        self._axes_cache: Optional[Dict[str, AxisProperties]] = None
    
    def _read_registry_values(self, key_path: str) -> Dict[str, Any]:
        """Read all values from a registry key"""
        values = {}
        
        try:
            with winreg.OpenKey(  # type: ignore[attr-defined]
                winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ  # type: ignore[attr-defined]
            ) as key:
                i = 0
                while True:
                    try:
                        name, value, reg_type = winreg.EnumValue(key, i)  # type: ignore[attr-defined]
                        values[name] = value
                        i += 1
                    except OSError:
                        break
        except Exception as e:
            logger.error(f"Error reading registry key {key_path}: {e}")
        
        return values
    
    def fetch_axis_properties(self, axis: str) -> Optional[AxisProperties]:
        """
        Fetch properties for a specific axis (X, Y, Z, or W)
        
        Args:
            axis: Axis name ('X', 'Y','Z', or 'W')
            
        Returns:
            AxisProperties object or None if not found
        """
        axis = axis.upper()
        if axis not in ['X', 'Y', 'Z', 'W']:
            logger.error(f"Invalid axis: {axis}. Must be X, Y, Z, or W")
            return None
        
        axis_path = f"{self.profile_path}\\Axes\\{axis}"
        
        try:
            data = self._read_registry_values(axis_path)
            
            if not data:
                logger.warning(f"No data found for axis {axis}")
                return None
            
            properties = AxisProperties.from_registry_data(data)
            logger.info(f"Fetched properties for {axis} axis: {properties}")
            return properties
            
        except Exception as e:
            logger.error(f"Error fetching axis {axis} properties: {e}")
            return None
    
    def fetch_all_axes(self) -> Dict[str, AxisProperties]:
        """
        Fetch properties for all axes (X, Y, Z)
        
        Returns:
            Dictionary mapping axis name to AxisProperties
        """
        if self._axes_cache is not None:
            return self._axes_cache
        
        axes = {}
        for axis_name in ['X', 'Y', 'Z']:
            props = self.fetch_axis_properties(axis_name)
            if props:
                axes[axis_name] = props
        
        self._axes_cache = axes
        logger.info(f"Fetched properties for {len(axes)} axes")
        return axes
    
    def list_available_profiles(self) -> list[str]:
        """
        List all available Bravo profiles
        
        Returns:
            List of profile names
        """
        profiles = []
        
        try:
            with winreg.OpenKey(  # type: ignore[attr-defined]
                winreg.HKEY_LOCAL_MACHINE, self.BASE_PATH, 0, winreg.KEY_READ  # type: ignore[attr-defined]
            ) as base_key:
                i = 0
                while True:
                    try:
                        profile_name = winreg.EnumKey(base_key, i)  # type: ignore[attr-defined]
                        profiles.append(profile_name)
                        i += 1
                    except OSError:
                        break
        except Exception as e:
            logger.error(f"Error listing profiles: {e}")
        
        logger.info(f"Found {len(profiles)} profiles: {profiles}")
        return profiles
    
    def get_profile_info(self) -> Dict[str, Any]:
        """
        Get general information about the current profile
        
        Returns:
            Dictionary with profile information
        """
        try:
            data = self._read_registry_values(self.profile_path)
            logger.info(f"Profile info for '{self.profile_name}': {len(data)} entries")
            return data
        except Exception as e:
            logger.error(f"Error getting profile info: {e}")
            return {}


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create registry reader
    bravo_reg = BravoRegistry("Mol Bio Bravo")
    
    # List available profiles
    profiles = bravo_reg.list_available_profiles()
    print(f"\nAvailable profiles: {profiles}")
    
    # Fetch single axis
    y_props = bravo_reg.fetch_axis_properties('Y')
    if y_props:
        print("\nY-axis properties:")
        print(f"  Homing offset: {y_props.homing_offset}")
        print(f"  Homing acceleration: {y_props.homing_acceleration}")
        print(f"  Homing velocity: {y_props.homing_velocity}")
    
    # Fetch all axes
    all_axes = bravo_reg.fetch_all_axes()
    print(f"\nAll axes: {all_axes.keys()}")