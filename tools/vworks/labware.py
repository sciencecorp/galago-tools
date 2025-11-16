import winreg
import json
import argparse
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class VWorksLabware:
    """Handler for VWorks labware registry operations"""
    
    BASE_PATH = r"SOFTWARE\WOW6432Node\Velocity11\Shared\Labware\Labware_Entries"
    
    def __init__(self) -> None:
        self._labware_cache: Optional[Dict[str, Dict[str, Any]]] = None
    
    def fetch_all(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all labware from VWorks registry"""
        all_labware = {}

        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, self.BASE_PATH, 0, winreg.KEY_READ
            ) as base_key:
                i = 0
                while True:
                    try:
                        entry_name = winreg.EnumKey(base_key, i)
                        entry_path = f"{self.BASE_PATH}\\{entry_name}"
                        
                        with winreg.OpenKey(
                            winreg.HKEY_LOCAL_MACHINE, entry_path, 0, winreg.KEY_READ
                        ) as entry_key:
                            entry_data = {}
                            j = 0
                            while True:
                                try:
                                    name, value, reg_type = winreg.EnumValue(entry_key, j)
                                    entry_data[name] = value
                                    j += 1
                                except WindowsError:
                                    break
                        
                        all_labware[entry_name] = entry_data
                        i += 1
                    except WindowsError:
                        break
            
            logger.info(f"Found {len(all_labware)} labware entries in registry")
            self._labware_cache = all_labware
            return all_labware

        except Exception as e:
            logger.error(f"Error fetching labware: {e}")
            return {}

    def filter(
        self,
        labware_dict: Optional[Dict[str, Dict[str, Any]]] = None,
        name_contains: Optional[str] = None,
        num_wells: Optional[int] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Filter labware by name or number of wells"""
        if labware_dict is None:
            labware_dict = self._labware_cache or self.fetch_all()
        
        filtered = {}
        
        for name, data in labware_dict.items():
            # Filter by name
            if name_contains and name_contains.lower() not in name.lower():
                continue
            
            # Filter by exact number of wells
            if num_wells:
                wells = int(data.get("NUMBER_OF_WELLS", 0))
                if wells != num_wells:
                    continue
            
            filtered[name] = data
        
        logger.info(f"Filtered to {len(filtered)} labware entries")
        return filtered

    def export_to_text(self, filename: Optional[str] = None) -> Optional[str]:
        """Export all labware registry data to a text file"""
        if filename is None:
            filename = f"vworks_labware_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, self.BASE_PATH, 0, winreg.KEY_READ
            ) as base_key:
                with open(filename, "w") as f:
                    f.write("VELOCITY11 LABWARE REGISTRY EXPORT\n")
                    f.write("=" * 50 + "\n\n")

                    i = 0
                    while True:
                        try:
                            entry_name = winreg.EnumKey(base_key, i)
                            f.write(f"ENTRY: {entry_name}\n")
                            f.write("-" * 30 + "\n")

                            entry_path = f"{self.BASE_PATH}\\{entry_name}"
                            with winreg.OpenKey(
                                winreg.HKEY_LOCAL_MACHINE, entry_path, 0, winreg.KEY_READ
                            ) as entry_key:
                                j = 0
                                while True:
                                    try:
                                        name, value, reg_type = winreg.EnumValue(entry_key, j)
                                        type_str = {
                                            winreg.REG_SZ: "REG_SZ",
                                            winreg.REG_DWORD: "REG_DWORD",
                                            winreg.REG_BINARY: "REG_BINARY",
                                        }.get(reg_type, f"REG_TYPE_{reg_type}")

                                        f.write(f"  {name}: {value} ({type_str})\n")
                                        j += 1
                                    except WindowsError:
                                        break

                            f.write("\n")
                            i += 1
                        except WindowsError:
                            break

            logger.info(f"Registry data exported to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error exporting registry data: {e}")
            return None

    def export_to_json(self, filename: Optional[str] = None) -> Optional[str]:
        """Export all labware data to JSON format"""
        if filename is None:
            filename = f"vworks_labware_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        all_data = self.fetch_all()
        
        try:
            with open(filename, "w") as f:
                json.dump(all_data, f, indent=2, default=str)

            logger.info(f"Registry data exported to JSON: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return None

def main() -> None:
    """CLI interface for VWorks labware operations"""
    parser = argparse.ArgumentParser(
        description="Access and export VWorks labware from registry"
    )
    parser.add_argument(
        "--name-contains",
        help="Filter by labware name (case-insensitive)",
    )
    parser.add_argument(
        "--num-wells",
        type=int,
        help="Filter by number of wells (e.g., 96, 384, 1536)",
    )
    parser.add_argument(
        "--export-json",
        action="store_true",
        help="Export to JSON file",
    )
    parser.add_argument(
        "--export-text",
        action="store_true",
        help="Export to text file",
    )
    parser.add_argument(
        "--output",
        help="Output filename (optional)",
    )
    
    args = parser.parse_args()
    
    vworks = VWorksLabware()
    
    # Handle export operations
    if args.export_json:
        vworks.export_to_json(args.output)
        return
    
    if args.export_text:
        vworks.export_to_text(args.output)
        return
    
    # Default: fetch and display filtered labware
    labware = vworks.fetch_all()
    filtered = vworks.filter(
        labware,
        name_contains=args.name_contains,
        num_wells=args.num_wells,
    )
    
    print(f"\nFound {len(filtered)} matching labware entries:")
    for name in filtered.keys():
        print(f"  - {name}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()