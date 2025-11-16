"""
Bravo driver that uses VWorks as a proxy to instantiate and control the ActiveX object.
This avoids all the COM threading and event handling issues.
"""

import os
import logging
import time
from typing import Optional, Any, List
from tools.base_server import ABCToolDriver
from tools.vworks.driver import VWorksDriver
import tempfile


class BravoViaVWorksDriver(ABCToolDriver):
    """
    Control Bravo by generating VWorks protocols that execute JavaScript with ActiveX.
    This leverages VWorks' proven ability to instantiate and use the Bravo control.
    """
    
    def __init__(self, profile: str = "Mol Bio Bravo", device_file: Optional[str] = None):
        self.profile = profile
        self.vworks = VWorksDriver(init_com=True)
        self.vworks.login()
        self._initialized = False
        
        # Device file - create a minimal one if needed
        if device_file:
            self.device_file = device_file
        else:
            # Create a minimal device file
            self.device_file = self._ensure_device_file()
        
        # Keep track of the bravo variable name for subsequent calls
        self.bravo_var = "bravo"
        
        # Buffer commands to execute together
        self._command_buffer: List[dict] = []
    
    def _ensure_device_file(self) -> str:
        """Create a minimal device file if one doesn't exist"""
        device_dir = r'C:\VWorks Workspace\Device Files'
        os.makedirs(device_dir, exist_ok=True)
        
        device_file = os.path.join(device_dir, 'bravo_minimal.dev')
        
        # Check if it already exists
        if os.path.exists(device_file):
            return device_file
        
        # Create minimal device file XML
        minimal_device = '''<?xml version='1.0' encoding='ASCII' ?>
            <Velocity11 file='Device_Data' md5sum='749176fa41bf04413021489f2ba27be3' version='2.0' >
                <Devices >
                </Devices>
            </Velocity11>'''
        
        try:
            with open(device_file, 'w', encoding='ASCII') as f:
                f.write(minimal_device)
            logging.info(f"Created minimal device file: {device_file}")
        except Exception as e:
            logging.warning(f"Could not create device file: {e}")
            # Fall back to empty string - VWorks might allow it
            return ""
        
        return device_file
        
    def _escape_for_xml_attribute(self, script: str) -> str:
        """
        Escape JavaScript for use in XML attribute.
        Must handle newlines, quotes, and special XML characters.
        """
        # First collapse all whitespace and newlines to single spaces
        script = ' '.join(script.split())
        
        # Escape XML special characters in correct order
        # IMPORTANT: & must be first!
        script = script.replace('&', '&amp;')
        script = script.replace('<', '&lt;')
        script = script.replace('>', '&gt;')
        
        # Replace double quotes with &quot; for XML attribute
        script = script.replace('"', '&quot;')
        
        # VWorks uses single quotes for attribute delimiters, so escape any single quotes in content
        script = script.replace("'", '&apos;')
        
        return script
    
    def _create_protocol_xml(self, tasks: list[dict]) -> str:
        """
        Create a VWorks protocol XML with JavaScript tasks.
        
        Args:
            tasks: List of dicts with 'description' and 'script' keys
        """
        # Build XML as string
        xml_parts = [
            "<?xml version='1.0' encoding='ASCII' ?>",
            "<Velocity11 file='Protocol_Data' md5sum='' version='2.0' >",
            f"<File_Info AllowSimultaneousRun='1' AutoExportGanttChart='0' "
            f"AutoLoadRacks='When the main protocol starts' AutoUnloadRacks='0' "
            f"AutomaticallyLoadFormFile='1' Barcodes_Directory='' ClearInventory='0' "
            f"DeleteHitpickFiles='1' Description='' Device_File='{self.device_file}' "
            f"Display_User_Task_Descriptions='1' DynamicAssignPlateStorageLoad='0' "
            f"FinishScript='' Form_File='' HandlePlatesInInstance='1' ImportInventory='0' "
            f"InventoryFile='' Notes='' PipettePlatesInInstanceOrder='0' Protocol_Alias='' "
            f"StartScript='' Use_Global_JS_Context='1' />",
            "<Processes >",
            "<Main_Processes >",
            "<Process >",
            "<Minimized >0</Minimized>"
        ]
        
        # Add each task
        for i, task in enumerate(tasks, 1):
            # Properly escape the script for XML attribute
            script = self._escape_for_xml_attribute(task['script'])
            description = task.get('description', 'JavaScript')
            estimated_time = task.get('estimated_time', 5.0)
            
            xml_parts.extend([
                "<Task Name='BuiltIn::JavaScript' >",
                "<Enable_Backup >0</Enable_Backup>",
                "<Task_Disabled >0</Task_Disabled>",
                "<Task_Skipped >0</Task_Skipped>",
                "<Has_Breakpoint >0</Has_Breakpoint>",
                "<Advanced_Settings >",
                f"<Setting Name='Estimated time' Value='{estimated_time}' />",
                "</Advanced_Settings>",
                f"<TaskScript Name='TaskScript' Value='{script}' />",
                "<Parameters >",
                f"<Parameter Category='Task Description' Name='Task number' Value='{i}' />",
                f"<Parameter Category='Task Description' Name='Task description' Value='{description}' />",
                "<Parameter Category='Task Description' Name='Use default task description' Value='0' />",
                "</Parameters>",
                "</Task>"
            ])
        
        # Close out the structure
        xml_parts.extend([
            "<Plate_Parameters >",
            "<Parameter Name='Plate name' Value='process - 1' />",
            "<Parameter Name='Plate type' Value='' />",
            "<Parameter Name='Simultaneous plates' Value='1' />",
            "<Parameter Name='Plates have lids' Value='0' />",
            "<Parameter Name='Plates enter the system sealed' Value='0' />",
            "<Parameter Name='Use single instance of plate' Value='0' />",
            "<Parameter Name='Automatically update labware' Value='0' />",
            "<Parameter Name='Enable timed release' Value='0' />",
            "<Parameter Name='Release time' Value='30' />",
            "<Parameter Name='Auto managed counterweight' Value='0' />",
            "<Parameter Name='Barcode filename' Value='No Selection' />",
            "<Parameter Name='Has header' Value='' />",
            "<Parameter Name='Barcode or header South' Value='No Selection' />",
            "<Parameter Name='Barcode or header West' Value='No Selection' />",
            "<Parameter Name='Barcode or header North' Value='No Selection' />",
            "<Parameter Name='Barcode or header East' Value='No Selection' />",
            "</Plate_Parameters>",
            "<Quarantine_After_Process >0</Quarantine_After_Process>",
            "</Process>",
            "</Main_Processes>",
            "</Processes>",
            "</Velocity11>"
        ])
        
        return '\n'.join(xml_parts)
    
    def _execute_buffer(self) -> None:
        """Execute all buffered commands as a single protocol"""
        if not self._command_buffer:
            return
        
        # Create temporary protocol file
        xml_content = self._create_protocol_xml(self._command_buffer)
        
        # Create temp file in VWorks Protocol Files directory
        temp_dir = r'C:\VWorks Workspace\Protocol Files'
        os.makedirs(temp_dir, exist_ok=True)
        
        # Use a more deterministic name for debugging
        protocol_path = os.path.join(temp_dir, f'bravo_batch_{int(time.time())}.pro')
        
        try:
            with open(protocol_path, 'w', encoding='ASCII') as f:
                f.write(xml_content)
            
            logging.info(f"Executing batch protocol with {len(self._command_buffer)} tasks: {protocol_path}")
            logging.debug(f"Protocol content:\n{xml_content}")
            
            self.vworks.run_protocol(protocol_path)
            
            # Clear the buffer after successful execution
            self._command_buffer = []
            
        finally:
            # Clean up temp file
            try:
                if os.path.exists(protocol_path):
                    time.sleep(0.5)  # Give VWorks time to finish with file
                    os.unlink(protocol_path)
            except Exception as e:
                logging.warning(f"Could not delete temp protocol: {e}")
    
    def _add_command(self, script: str, description: str, estimated_time: float = 5.0) -> None:
        """Add a command to the buffer"""
        self._command_buffer.append({
            'script': script,
            'description': description,
            'estimated_time': estimated_time
        })
    
    def initialize(self, profile: Optional[str] = None) -> None:
        """Initialize Bravo via VWorks"""
        if profile:
            self.profile = profile
        
        # Single-line JavaScript that will be escaped properly
        init_script = f'var {self.bravo_var} = new ActiveX("HW.HomewoodCtrl.1"); {self.bravo_var}.CreateControl(); {self.bravo_var}.Blocking = true; var result = {self.bravo_var}.Initialize("{self.profile}"); if (result != 0) {{ var error = {self.bravo_var}.GetLastError(); throw new Error("Initialize failed: " + error); }}'
        
        self._add_command(init_script, "Initialize Bravo", 10.0)
        self._initialized = True
        logging.info(f"✓ Bravo initialization queued for profile: {self.profile}")
    
    def set_labware_at_location(self, plate_location: int, labware_type: str) -> None:
        """Set labware at location"""
        if not self._initialized:
            raise RuntimeError("Bravo not initialized")
        
        script = f'var result = {self.bravo_var}.SetLabwareAtLocation({plate_location}, "{labware_type}"); if (result != 0) {{ throw new Error("SetLabwareAtLocation failed: " + {self.bravo_var}.GetLastError()); }}'
        
        self._add_command(script, f"Set labware '{labware_type}' at location {plate_location}")
        logging.info(f"✓ Set labware command queued")
    
    def tips_on(self, plate_location: int) -> None:
        """Pick up tips"""
        if not self._initialized:
            raise RuntimeError("Bravo not initialized")
        
        script = f'var result = {self.bravo_var}.TipsOn({plate_location}); if (result != 0) {{ throw new Error("TipsOn failed: " + {self.bravo_var}.GetLastError()); }}'
        
        self._add_command(script, f"Pick up tips at location {plate_location}", 8.0)
        logging.info(f"✓ TipsOn command queued")
    
    def tips_off(self, plate_location: int) -> None:
        """Eject tips"""
        if not self._initialized:
            raise RuntimeError("Bravo not initialized")
        
        script = f'var result = {self.bravo_var}.TipsOff({plate_location}); if (result != 0) {{ throw new Error("TipsOff failed: " + {self.bravo_var}.GetLastError()); }}'
        
        self._add_command(script, f"Eject tips at location {plate_location}", 8.0)
        logging.info(f"✓ TipsOff command queued")
    
    def move_to_location(self, plate_location: int, only_z: bool = False) -> None:
        """Move to location"""
        if not self._initialized:
            raise RuntimeError("Bravo not initialized")
        
        only_z_str = "true" if only_z else "false"
        script = f'var result = {self.bravo_var}.MoveToLocation({plate_location}, {only_z_str}); if (result != 0) {{ throw new Error("MoveToLocation failed: " + {self.bravo_var}.GetLastError()); }}'
        
        self._add_command(script, f"Move to location {plate_location}", 6.0)
        logging.info(f"✓ MoveToLocation command queued")
    
    def aspirate(self, volume: float, plate_location: int,
                 distance_from_well_bottom: float = 0.0,
                 pre_aspirate_volume: float = 0.0,
                 post_aspirate_volume: float = 0.0,
                 retract_distance_per_microliter: float = 0.0) -> None:
        """Aspirate liquid"""
        if not self._initialized:
            raise RuntimeError("Bravo not initialized")
        
        script = f'var result = {self.bravo_var}.Aspirate({volume}, {pre_aspirate_volume}, {post_aspirate_volume}, {plate_location}, {distance_from_well_bottom}, {retract_distance_per_microliter}); if (result != 0) {{ throw new Error("Aspirate failed: " + {self.bravo_var}.GetLastError()); }}'
        
        self._add_command(script, f"Aspirate {volume}µL from location {plate_location}", 8.0)
        logging.info(f"✓ Aspirate command queued")
    
    def dispense(self, volume: float, empty_tips: bool, blow_out_volume: float,
                 plate_location: int, distance_from_well_bottom: float = 0.0,
                 retract_distance_per_microliter: float = 0.0) -> None:
        """Dispense liquid"""
        if not self._initialized:
            raise RuntimeError("Bravo not initialized")
        
        empty_tips_str = "true" if empty_tips else "false"
        script = f'var result = {self.bravo_var}.Dispense({volume}, {empty_tips_str}, {blow_out_volume}, {plate_location}, {distance_from_well_bottom}, {retract_distance_per_microliter}); if (result != 0) {{ throw new Error("Dispense failed: " + {self.bravo_var}.GetLastError()); }}'
        
        self._add_command(script, f"Dispense {volume}µL to location {plate_location}", 8.0)
        logging.info(f"✓ Dispense command queued")
    
    def show_diagnostics(self) -> None:
        """Show diagnostics dialog"""
        script = f'{self.bravo_var}.ShowDiagsDialog(true, 1);'
        
        self._add_command(script, "Show diagnostics dialog", 5.0)
        logging.info("✓ ShowDiagnostics command queued")
    
    def execute(self) -> None:
        """Execute all queued commands"""
        logging.info(f"Executing {len(self._command_buffer)} queued commands...")
        self._execute_buffer()
        logging.info("✓ All commands executed successfully")
    
    def close(self) -> None:
        """Close Bravo and VWorks"""
        if self._initialized and self._command_buffer:
            # Add close command to buffer
            script = f'{self.bravo_var}.Close();'
            self._add_command(script, "Close Bravo", 2.0)
            
            # Execute everything including close
            try:
                self._execute_buffer()
            except Exception as e:
                logging.warning(f"Error during close execution: {e}")
        
        self.vworks.close()
        self._initialized = False
        logging.info("✓ Bravo and VWorks closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Test script
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    
    print("=" * 60)
    print("BRAVO VIA VWORKS DRIVER TEST")
    print("=" * 60)
    
    try:
        with BravoViaVWorksDriver("Mol Bio Bravo") as bravo:
            print("\n--- Building command sequence ---")
            
            # Queue all commands
            bravo.initialize()
            # bravo.set_labware_at_location(2, "96 V11 LT250 Tip Box Standard")
            # bravo.move_to_location(1)
            # bravo.tips_on(2)
            # bravo.tips_off(2)
            bravo.show_diagnostics()
            
            print("\n--- Executing all commands as single protocol ---")
            bravo.execute()
            
            print("\n✓ All operations completed successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()