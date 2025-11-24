"""
Bravo driver that generates VWorks protocols dynamically.
Commands are queued and executed as a batch protocol.
"""

import os
import logging
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from tools.vworks.driver import VWorksDriver
from pathlib import Path
from tools.base_server import ABCToolDriver

TASK_TYPE_BY_NAME = {
    'Mix': 4096,
    'Aspirate': 1,
    'Dispense': 2,
    'Tips On': 16,
    'Tips Off': 32,
    'Move To Location': 1024,
    'Initialize axis': 1024
}


@dataclass
class BravoTask:
    """Represents a single Bravo task in a protocol"""
    name: str
    task_type: int
    parameters: Dict[str, Any]
    description: str = ""
    estimated_time: float = 5.0
    pipette_head: Optional[Dict[str, Any]] = None


class BravoDriver(ABCToolDriver):
    """Builds VWorks protocol XML dynamically"""
    
    def __init__(self, 
                device_file: str, 
                device_name: Optional[str] = None
                ) -> None:
        self.device_file = device_file
        self.tasks: List[BravoTask] = []
        self.device_name = device_name if device_name else "Agilent Bravo - 1"
        self.location_name = "Default Location"
        
        # Parse device file to get device info
        self._parse_device_file()
    
    def _parse_device_file(self) -> None:
            """Extract device and location info from device file"""
            if not os.path.exists(self.device_file):
                logging.warning(f"Device file not found: {self.device_file}")
                raise FileNotFoundError(f"Device file not found: {self.device_file}")
            
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(self.device_file)
                root = tree.getroot()
                
                # Find all Bravo devices
                devices = root.findall(".//Device[@Object_Type='Bravo']")
                
                if len(devices) == 0:
                    logging.warning("No Bravo devices found in device file")
                elif len(devices) > 1:
                    device_names = [d.get('Name', 'Unknown') for d in devices]
                    logging.warning(
                        f"Multiple Bravo devices found in configuration file: {', '.join(device_names)}. "
                        f"Defaulting to first device: '{device_names[0]}'. "
                        f"Specify device_name if you would like to use a different device."
                    )
                    self.device_name = devices[0].get('Name', self.device_name)
                    logging.info(f"Using Bravo device: {self.device_name}")
                else:
                    # Single device found
                    self.device_name = devices[0].get('Name', self.device_name)
                    logging.info(f"Found Bravo device: {self.device_name}")
                        
            except Exception as e:
                logging.error(f"Error parsing device file: {e}")
    
    def add_subprocess_task(self, deck_configuration: Dict[int, str]) -> None:
        """Add subprocess initialization task with labware configuration
        
        Args:
            deck_configuration: Dictionary mapping position (1-9) to labware name
        """
        params = {
            'Sub-process name': 'Bravo SubProcess 1',
            'Display confirmation': "Don't display"
        }
        
        # Add labware configuration for positions 1-9
        for pos in range(1, 10):
            params[str(pos)] = deck_configuration.get(pos, '<use default>')
        
        task = BravoTask(
            name='Bravo::SubProcess',
            task_type=0,
            parameters=params,
            description='Initialize Bravo subprocess',
            estimated_time=10.0
        )
        self.tasks.append(task)
    
    def add_move_to_location(self, plate_location: int) -> None:
        """Add move to location task
        
        Args:
            plate_location: Location to move to
        """
        task = BravoTask(
            name='Bravo::secondary::Move To Location',
            task_type=TASK_TYPE_BY_NAME['Move To Location'],
            parameters={
                'Location': str(plate_location),
                'Task description': f'Move To Location {plate_location} (Bravo)',
                'Use default task description': '1'
            },
            description=f'Move to location {plate_location}',
            estimated_time=26.0,
            pipette_head=self._get_default_pipette_head()
        )
        self.tasks.append(task)

    def add_tips_on(self, plate_location: int) -> None:
        """Add tips on task
        
        Args:
            plate_location: Location of tip box
        """
        task = BravoTask(
            name='Bravo::secondary::Tips On',
            task_type=TASK_TYPE_BY_NAME['Tips On'],
            parameters={
                'Location, plate': str(plate_location),
                'Location, location': '<auto-select>',
                'Allow automatic tracking of tip usage': '0',
                'Well selection': self._get_well_selection_xml(),
                'Task description': f'Tips On at {plate_location} (Bravo)',
                'Use default task description': '1'
            },
            description=f'Pick up tips at location {plate_location}',
            estimated_time=5.0,
            pipette_head=self._get_default_pipette_head()
        )
        self.tasks.append(task)

    
    def add_tips_off(self, plate_location: int, mark_used: bool = True) -> None:
        """Add tips off task
        
        Args:
            plate_location: Location of tip disposal
            mark_used: Whether to mark tips as used (This is only relevant within the VWorks context, we can track tips outside of VWorks)
        """
        task = BravoTask(
            name='Bravo::secondary::Tips Off',
            task_type=TASK_TYPE_BY_NAME['Tips Off'],
            parameters={
                'Location, plate': str(plate_location),
                'Location, location': '<auto-select>',
                'Allow automatic tracking of tip usage': '0',
                'Mark tips as used': '1' if mark_used else '0',
                'Well selection': self._get_well_selection_xml(),
                'Task description': f'Tips Off at {plate_location} (Bravo)',
                'Use default task description': '1'
            },
            description=f'Eject tips at location {plate_location}',
            estimated_time=5.0,
            pipette_head=self._get_default_pipette_head()
        )
        self.tasks.append(task)
    
    def add_aspirate(self, 
                    location: int, 
                    volume: float,
                    pre_aspirate_volume: float = 0.0,
                    post_aspirate_volume: float = 0.0,
                    liquid_class: str = '',
                    distance_from_well_bottom: float = 2.0,
                    retract_distance_per_microliter: float = 0.0,
                    pipette_technique: str = '',
                    perform_tip_touch: bool = False,
                    tip_touch_side: str = 'None',
                    tip_touch_retract_distance: float = 0.0,
                    tip_touch_horizontal_offset: float = 0.0) -> None:
        """Add aspirate task
        
        Args:
            location: Location to aspirate from
            volume: Volume to aspirate (µL)
            pre_aspirate_volume: Volume to pre-aspirate (µL)
            post_aspirate_volume: Volume to post-aspirate (µL)
            liquid_class: Liquid class name
            distance_from_well_bottom: Distance from well bottom (mm)
            retract_distance_per_microliter: Amount the Z axis retracts per µL aspirated (mm/µL)
            pipette_technique: Pipette technique name
            perform_tip_touch: Whether to perform tip touch after aspirate
            tip_touch_side: Side(s) to perform tip touch on
            tip_touch_retract_distance: Distance to retract after tip touch (mm) (-20 to 50)
            tip_touch_horizontal_offset: Horizontal offset for tip touch (mm) (-9 to 5)
        """
        assert volume > 0 and volume <= 250, "Volume must be between 0 and 250 µL"
        assert distance_from_well_bottom >= 0, "Distance from well bottom must be non-negative"
        assert retract_distance_per_microliter >= 0, "Retract distance per microliter must be non-negative"
        assert tip_touch_side in ['None', 'South', 'West', 'North', 'Front', 'East', 
                                'South/North', 'West/East', 'West/East/South/North'], "Invalid tip touch side"
        assert tip_touch_retract_distance >= -20 and tip_touch_retract_distance <= 50, "Tip touch retract distance must be between -20 and 50 mm"
        assert tip_touch_horizontal_offset >= -9 and tip_touch_horizontal_offset <= 5, "Tip touch horizontal offset must be between -9 and 5 mm"
        
        task = BravoTask(
            name='Bravo::secondary::Aspirate',
            task_type=TASK_TYPE_BY_NAME['Aspirate'],
            parameters={
                'Location, plate': str(location),
                'Location, location': '<auto-select>',
                'Volume': str(volume),
                'Pre-aspirate volume': str(pre_aspirate_volume),
                'Post-aspirate volume': str(post_aspirate_volume),
                'Liquid class': liquid_class,
                'Distance from well bottom': str(distance_from_well_bottom),
                'Dynamic tip extension': str(retract_distance_per_microliter),
                'Perform tip touch': '1' if perform_tip_touch else '0',
                'Which sides to use for tip touch': tip_touch_side,
                'Tip touch retract distance': str(tip_touch_retract_distance),
                'Tip touch horizontal offset': str(tip_touch_horizontal_offset),
                'Well selection': self._get_well_selection_xml(),
                'Pipette technique': pipette_technique,
                'Task description': f'Aspirate {volume}µL from {location} (Bravo)',
                'Use default task description': '1'
            },
            description=f'Aspirate {volume}µL from location {location}',
            estimated_time=5.0,
            pipette_head=self._get_default_pipette_head()
        )
        self.tasks.append(task)


    def add_dispense(self, 
                    location: int,
                    empty_tips: bool = False,
                    volume: float = 0.0,
                    blowout_volume: float = 0.0,
                    liquid_class: str = '',
                    distance_from_well_bottom: float = 2.0,
                    retract_distance_per_microliter: float = 0.0,
                    pipette_technique: str = '',
                    perform_tip_touch: bool = False,
                    tip_touch_side: str = 'None',
                    tip_touch_retract_distance: float = 0.0,
                    tip_touch_horizontal_offset: float = 0.0) -> None:
        """Add dispense task
        
        Args:
            location: Location to dispense to
            empty_tips: Whether to empty tips completely
            volume: Volume to dispense (µL)
            blowout_volume: Volume to blowout after dispense (µL)
            liquid_class: Liquid class name
            distance_from_well_bottom: Distance from well bottom (mm)
            retract_distance_per_microliter: Amount the Z axis retracts per µL dispensed (mm/µL)
            pipette_technique: Pipette technique name
            perform_tip_touch: Whether to perform tip touch after dispense
            tip_touch_side: Side(s) to perform tip touch on
            tip_touch_retract_distance: Distance to retract after tip touch (mm) (-20 to 50)
            tip_touch_horizontal_offset: Horizontal offset for tip touch (mm) (-9 to 5)
        """
        assert volume >= 0 and volume <= 250, "Volume must be between 0 and 250 µL"
        assert distance_from_well_bottom >= 0, "Distance from well bottom must be non-negative"
        assert retract_distance_per_microliter >= 0, "Retract distance per microliter must be non-negative"
        assert tip_touch_side in ['None', 'South', 'West', 'North', 'Front', 'East', 
                                'South/North', 'West/East', 'West/East/South/North'], "Invalid tip touch side"
        assert tip_touch_retract_distance >= -20 and tip_touch_retract_distance <= 50, "Tip touch retract distance must be between -20 and 50 mm"
        assert tip_touch_horizontal_offset >= -9 and tip_touch_horizontal_offset <= 5, "Tip touch horizontal offset must be between -9 and 5 mm"
        
        task = BravoTask(
            name='Bravo::secondary::Dispense',
            task_type=TASK_TYPE_BY_NAME['Dispense'],
            parameters={
                'Location, plate': str(location),
                'Location, location': '<auto-select>',
                'Empty tips': '1' if empty_tips else '0',
                'Volume': str(volume),
                'Blowout volume': str(blowout_volume),
                'Liquid class': liquid_class,
                'Distance from well bottom': str(distance_from_well_bottom),
                'Dynamic tip retraction': str(retract_distance_per_microliter),
                'Perform tip touch': '1' if perform_tip_touch else '0',
                'Which sides to use for tip touch': tip_touch_side,
                'Tip touch retract distance': str(tip_touch_retract_distance),
                'Tip touch horizontal offset': str(tip_touch_horizontal_offset),
                'Well selection': self._get_well_selection_xml(),
                'Pipette technique': pipette_technique,
                'Task description': f'Dispense {volume}µL to {location} (Bravo)',
                'Use default task description': '1'
            },
            description=f'Dispense {volume}µL to location {location}',
            estimated_time=5.0,
            pipette_head=self._get_default_pipette_head()
        )
        self.tasks.append(task)

    
    def add_mix(self, 
            location: int, 
            volume: float, 
            pre_aspirate_volume: float = 0.0, 
            blowout_volume: float = 0.0,
            liquid_class: str = '', 
            cycles: int = 3,
            retract_distance_per_microliter: float = 0.0,
            pipette_technique: str = '',
            aspirate_distance: float = 2.0, 
            dispense_distance: float = 2.0,
            perform_tip_touch: bool = False,
            tip_touch_side: str = 'None', 
            tip_touch_retract_distance: float = 0.0,
            tip_touch_horizontal_offset: float = 0.0
                ) -> None:
        """Add mix task with dual height support"""
        task = BravoTask(
            name='Bravo::secondary::Mix [Dual Height]',
            task_type=TASK_TYPE_BY_NAME['Mix'],
            parameters={
                'Location, plate': str(location),
                'Location, location': '<auto-select>',
                'Volume': str(volume),
                'Pre-aspirate volume': str(pre_aspirate_volume),
                'Blowout volume': str(blowout_volume),
                'Liquid class': liquid_class,
                'Mix cycles': str(cycles),
                'Dynamic tip extension': str(retract_distance_per_microliter),
                'Aspirate distance': str(aspirate_distance),
                'Dispense at different distance': '1' if aspirate_distance != dispense_distance else '0',
                'Dispense distance': str(dispense_distance),
                'Perform tip touch': '1' if perform_tip_touch else '0',
                'Which sides to use for tip touch': tip_touch_side,
                'Tip touch retract distance': str(tip_touch_retract_distance),
                'Tip touch horizontal offset': str(tip_touch_horizontal_offset),
                'Well selection': self._get_well_selection_xml(),
                'Pipette technique': pipette_technique,
                'Task description': f'Mix {volume}µL x{cycles} at location {location} (Bravo)',
                'Use default task description': '1'
            },
            description=f'Mix {volume}µL with {cycles} cycles at location {location}',
            estimated_time=5.0,
            pipette_head=self._get_default_pipette_head()
        )
        self.tasks.append(task)
    
    def add_initialize_axis(self, axis: str = 'XYZ', force_home: bool = True) -> None:
        """Add axis initialization/homing task
        
        Args:
            axis: Axis to initialize - 'X', 'Y', 'Z', 'W', 'G', 'Zg
            force_home: Initialize even if already homed
        """
        valid_axes = ['X', 'Y', 'Z', 'W', 'G', 'Zg']
        if axis.upper() not in valid_axes:
            raise ValueError(f"Invalid axis '{axis}'. Must be one of {valid_axes}")
        
        task = BravoTask(
            name='Bravo::secondary::Initialize axis',
            task_type=TASK_TYPE_BY_NAME['Initialize axis'],
            parameters={
                'Axis': axis.upper(),
                'Initialize even if already homed': '1' if force_home else '0',
                'Task description': f'Initialize axis {axis} (Bravo)',
                'Use default task description': '1'
            },
            description=f'Initialize {axis} axis',
            estimated_time=15.0 if 'Z' in axis.upper() else 5.0,
            pipette_head=self._get_default_pipette_head()
        )
        self.tasks.append(task)
    
    def _get_default_pipette_head(self) -> Dict[str, Any]:
        """Get default 96-channel pipette head configuration"""
        return {
            'AssayMap': '0',
            'Disposable': '1',
            'HasTips': '1',
            'MaxRange': '251',
            'MinRange': '-41',
            'Name': '96LT, 200 µL Series III',
            'Mode': {
                'Channels': '0',
                'ColumnCount': '12',
                'RowCount': '8',
                'SubsetConfig': '0',
                'SubsetType': '0',
                'TipType': '1'
            }
        }
    
    def _get_well_selection_xml(self) -> str:
        """Generate well selection XML for single well A1 - properly escaped for XML attribute"""
        # This needs to be escaped since it's stored as a string inside an XML attribute
        return """&lt;?xml version=&apos;1.0&apos; encoding=&apos;ASCII&apos; ?&gt;
&lt;Velocity11 file=&apos;MetaData&apos; md5sum=&apos;9757f6c2d2ffcd4028d388c9a706d5ea&apos; version=&apos;1.0&apos; &gt;
\t&lt;WellSelection CanBe16QuadrantPattern=&apos;0&apos; CanBeLinked=&apos;0&apos; CanBeQuadrantPattern=&apos;0&apos; IsLinked=&apos;0&apos; IsQuadrantPattern=&apos;0&apos; OnlyOneSelection=&apos;1&apos; OverwriteHeadMode=&apos;0&apos; QuadrantPattern=&apos;0&apos; StartingQuadrant=&apos;1&apos; &gt;
\t\t&lt;PipetteHeadMode Channels=&apos;0&apos; ColumnCount=&apos;12&apos; RowCount=&apos;8&apos; SubsetConfig=&apos;0&apos; SubsetType=&apos;0&apos; TipType=&apos;1&apos; /&gt;
\t\t&lt;Wells &gt;
\t\t\t&lt;Well Column=&apos;0&apos; Row=&apos;0&apos; /&gt;
\t\t&lt;/Wells&gt;
\t&lt;/WellSelection&gt;
&lt;/Velocity11&gt;"""
    
    def build_xml(self) -> str:
        """Build complete protocol XML with proper formatting"""
        xml_parts = [
            "<?xml version='1.0' encoding='ASCII' ?>",
            "<Velocity11 file='Protocol_Data' md5sum='' version='2.0' >",
            f"\t<File_Info AllowSimultaneousRun='1' AutoExportGanttChart='0' "
            f"AutoLoadRacks='When the main protocol starts' AutoUnloadRacks='0' "
            f"AutomaticallyLoadFormFile='1' Barcodes_Directory='' ClearInventory='0' "
            f"DeleteHitpickFiles='1' Description='' Device_File='{self.device_file}' "
            f"Display_User_Task_Descriptions='1' DynamicAssignPlateStorageLoad='0' "
            f"FinishScript='' Form_File='' HandlePlatesInInstance='1' ImportInventory='0' "
            f"InventoryFile='' Notes='' PipettePlatesInInstanceOrder='0' Protocol_Alias='' "
            f"StartScript='' Use_Global_JS_Context='0' />",
            "\t<Processes >",
            "\t\t<Main_Processes >",
            "\t\t\t<Process >",
            "\t\t\t\t<Minimized >0</Minimized>"
        ]
        
        # Add subprocess task if it exists
        subprocess_task = None
        other_tasks = []
        for task in self.tasks:
            if task.name == 'Bravo::SubProcess':
                subprocess_task = task
            else:
                other_tasks.append(task)
        
        if subprocess_task:
            xml_parts.extend(self._build_subprocess_xml(subprocess_task))
        
        # Plate Parameters
        xml_parts.extend([
            "\t\t\t\t<Plate_Parameters >",
            "\t\t\t\t\t<Parameter Name='Plate name' Value='process - 1' />",
            "\t\t\t\t\t<Parameter Name='Plate type' Value='' />",
            "\t\t\t\t\t<Parameter Name='Simultaneous plates' Value='1' />",
            "\t\t\t\t\t<Parameter Name='Plates have lids' Value='0' />",
            "\t\t\t\t\t<Parameter Name='Plates enter the system sealed' Value='0' />",
            "\t\t\t\t\t<Parameter Name='Use single instance of plate' Value='0' />",
            "\t\t\t\t\t<Parameter Name='Automatically update labware' Value='0' />",
            "\t\t\t\t\t<Parameter Name='Enable timed release' Value='0' />",
            "\t\t\t\t\t<Parameter Name='Release time' Value='30' />",
            "\t\t\t\t\t<Parameter Name='Auto managed counterweight' Value='0' />",
            "\t\t\t\t\t<Parameter Name='Barcode filename' Value='No Selection' />",
            "\t\t\t\t\t<Parameter Name='Has header' Value='' />",
            "\t\t\t\t\t<Parameter Name='Barcode or header South' Value='No Selection' />",
            "\t\t\t\t\t<Parameter Name='Barcode or header West' Value='No Selection' />",
            "\t\t\t\t\t<Parameter Name='Barcode or header North' Value='No Selection' />",
            "\t\t\t\t\t<Parameter Name='Barcode or header East' Value='No Selection' />",
            "\t\t\t\t</Plate_Parameters>",
            "\t\t\t\t<Quarantine_After_Process >0</Quarantine_After_Process>",
            "\t\t\t</Process>"
        ])
        
        # Pipette_Process with other tasks
        if other_tasks and subprocess_task:
            xml_parts.extend(self._build_pipette_process_xml(subprocess_task, other_tasks))
        
        xml_parts.extend([
            "\t\t</Main_Processes>",
            "\t</Processes>",
            "</Velocity11>"
        ])
        
        return '\n'.join(xml_parts)
    
    def _build_subprocess_xml(self, task: BravoTask) -> List[str]:
        """Build subprocess task XML"""
        xml_parts = [
            "\t\t\t\t<Task Name='Bravo::SubProcess' >",
            "\t\t\t\t\t<Enable_Backup >0</Enable_Backup>",
            "\t\t\t\t\t<Task_Disabled >0</Task_Disabled>",
            "\t\t\t\t\t<Task_Skipped >0</Task_Skipped>",
            "\t\t\t\t\t<Has_Breakpoint >0</Has_Breakpoint>",
            "\t\t\t\t\t<Advanced_Settings />",
            "\t\t\t\t\t<TaskScript Name='TaskScript' Value='' />",
            "\t\t\t\t\t<Parameters >",
            f"\t\t\t\t\t\t<Parameter Category='' Name='Sub-process name' Value='{task.parameters['Sub-process name']}' />",
            f"\t\t\t\t\t\t<Parameter Category='Static labware configuration' Name='Display confirmation' Value=\"{task.parameters['Display confirmation']}\" />"
        ]
        
        # Add labware configuration
        for i in range(1, 10):
            labware = task.parameters.get(str(i), '<use default>')
            if labware == '<use default>':
                labware_escaped = '&lt;use default&gt;'
            else:
                labware_escaped = labware.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')
            xml_parts.append(f"\t\t\t\t\t\t<Parameter Category='Static labware configuration' Name='{i}' Value='{labware_escaped}' />")
        
        xml_parts.extend([
            "\t\t\t\t\t</Parameters>",
            "\t\t\t\t\t<Parameters >",
            f"\t\t\t\t\t\t<Parameter Centrifuge='0' Name='SubProcess_Name' Pipettor='1' Value='{task.parameters['Sub-process name']}' />",
            "\t\t\t\t\t</Parameters>",
            "\t\t\t\t</Task>"
        ])
        
        return xml_parts
    
    def _build_pipette_process_xml(self, subprocess_task: BravoTask, tasks: List[BravoTask]) -> List[str]:
        """Build pipette process with tasks"""
        xml_parts = [
            f"\t\t\t<Pipette_Process Name='{subprocess_task.parameters['Sub-process name']}' >",
            "\t\t\t\t<Minimized >0</Minimized>"
        ]
        
        # Add each task
        for i, task in enumerate(tasks, 1):
            xml_parts.extend(self._build_task_xml(task, i))
        
        # Devices section
        xml_parts.extend([
            "\t\t\t\t<Devices >",
            f"\t\t\t\t\t<Device Device_Name='{self.device_name}' Location_Name='{self.location_name}' />",
            "\t\t\t\t</Devices>",
            "\t\t\t\t<Parameters >",
            f"\t\t\t\t\t<Parameter Name='Display confirmation' Value=\"{subprocess_task.parameters['Display confirmation']}\" />"
        ])
        
        # Add labware config
        for i in range(1, 10):
            labware = subprocess_task.parameters.get(str(i), '<use default>')
            if labware == '<use default>':
                labware_escaped = '&lt;use default&gt;'
            else:
                labware_escaped = labware.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')
            xml_parts.append(f"\t\t\t\t\t<Parameter Name='{i}' Value='{labware_escaped}' />")
        
        xml_parts.extend([
            "\t\t\t\t</Parameters>",
            "\t\t\t\t<Dependencies />",
            "\t\t\t</Pipette_Process>"
        ])
        
        return xml_parts
    
    def _build_task_xml(self, task: BravoTask, task_num: int) -> List[str]:
        """Build individual task XML"""
        xml_parts = [
            f"\t\t\t\t<Task Name='{task.name}' Task_Type='{task.task_type}' >",
            "\t\t\t\t\t<Enable_Backup >0</Enable_Backup>",
            "\t\t\t\t\t<Task_Disabled >0</Task_Disabled>",
            "\t\t\t\t\t<Task_Skipped >0</Task_Skipped>",
            "\t\t\t\t\t<Has_Breakpoint >0</Has_Breakpoint>",
            "\t\t\t\t\t<Advanced_Settings >",
            f"\t\t\t\t\t\t<Setting Name='Estimated time' Value='{task.estimated_time}' />",
            "\t\t\t\t\t</Advanced_Settings>",
            "\t\t\t\t\t<TaskScript Name='TaskScript' Value='' />",
            "\t\t\t\t\t<Parameters >"
        ]
        
        # Add parameters
        for name, value in task.parameters.items():
            # Determine category
            category = ''
            if 'Task' in name or 'description' in name:
                category = 'Task Description'
            elif name in ['Volume', 'Pre-aspirate volume', 'Post-aspirate volume', 'Blowout volume', 'Empty tips']:
                category = 'Volume'
            elif name in ['Liquid class', 'Distance from well bottom', 'Dynamic tip extension', 'Dynamic tip retraction', 
                         'Well selection', 'Pipette technique', 'Mix cycles', 'Allow automatic tracking of tip usage', 'Mark tips as used']:
                category = 'Properties'
            elif 'Tip touch' in name or 'tip touch' in name:
                category = 'Tip Touch'
            elif 'distance' in name.lower() and 'Distance From Well Bottom' not in category:
                category = 'Distance From Well Bottom'
            
            # Well selection is already escaped, don't double escape
            if name == 'Well selection':
                value_str = str(value)
            else:
                value_str = str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')
            
            if category:
                xml_parts.append(f"\t\t\t\t\t\t<Parameter Category='{category}' Name='{name}' Value='{value_str}' />")
            else:
                xml_parts.append(f"\t\t\t\t\t\t<Parameter Category='' Name='{name}' Value='{value_str}' />")
        
        # Add task number if not present
        if 'Task number' not in task.parameters:
            xml_parts.append(f"\t\t\t\t\t\t<Parameter Category='Task Description' Name='Task number' Value='{task_num}' />")
        
        xml_parts.append("\t\t\t\t\t</Parameters>")
        
        # Add pipette head if present
        if task.pipette_head:
            head = task.pipette_head
            xml_parts.append(f"\t\t\t\t\t<PipetteHead AssayMap='{head['AssayMap']}' Disposable='{head['Disposable']}' "
                           f"HasTips='{head['HasTips']}' MaxRange='{head['MaxRange']}' MinRange='{head['MinRange']}' "
                           f"Name='{head['Name']}' >")
            
            mode = head['Mode']
            xml_parts.append(f"\t\t\t\t\t\t<PipetteHeadMode Channels='{mode['Channels']}' ColumnCount='{mode['ColumnCount']}' "
                           f"RowCount='{mode['RowCount']}' SubsetConfig='{mode['SubsetConfig']}' "
                           f"SubsetType='{mode['SubsetType']}' TipType='{mode['TipType']}' />")
            xml_parts.append("\t\t\t\t\t</PipetteHead>")
        
        xml_parts.append("\t\t\t\t</Task>")
        
        return xml_parts


class BravoVWorksDriver:
    """High-level Bravo driver using VWorks protocols"""
    
    def __init__(self, device_file: str) -> None:
        self.device_file = device_file
        self.vworks = VWorksDriver()
        self.builder = BravoDriver(device_file)
        self._initialized = False
        
        logging.info(f"Bravo driver initialized with device file: {device_file}")
    
    def move_to_location(self, plate_location: int) -> None:
        """Move to specified location
        
        Args:
            plate_location: Location to move to
        """
        if not self._initialized:
            raise RuntimeError("Bravo not initialized. Call initialize() first.")
        self.builder.add_move_to_location(plate_location)
        logging.info(f"✓ Move to location {plate_location} queued")

    def tips_on(self, plate_location: int) -> None:
        """Pick up tips at location
        
        Args:
            plate_location: Location of tip box
        """
        if not self._initialized:
            raise RuntimeError("Bravo not initialized. Call initialize() first.")
        self.builder.add_tips_on(plate_location)
        logging.info(f"✓ Tips on at location {plate_location} queued")

    def tips_off(self, plate_location: int, mark_used: bool = True) -> None:
        """Eject tips at location
        
        Args:
            plate_location: Location of tip disposal
            mark_used: Whether to mark tips as used
        """
        if not self._initialized:
            raise RuntimeError("Bravo not initialized. Call initialize() first.")
        self.builder.add_tips_off(plate_location, mark_used)
        logging.info(f"✓ Tips off at location {plate_location} queued")

    def aspirate(self, 
                location: int, 
                volume: float,
                pre_aspirate_volume: float = 0.0,
                post_aspirate_volume: float = 0.0,
                liquid_class: str = '',
                distance_from_well_bottom: float = 2.0,
                retract_distance_per_microliter: float = 0.0,
                pipette_technique: str = '',
                perform_tip_touch: bool = False,
                tip_touch_side: str = 'None',
                tip_touch_retract_distance: float = 0.0,
                tip_touch_horizontal_offset: float = 0.0) -> None:
        """Aspirate from location"""
        if not self._initialized:
            raise RuntimeError("Bravo not initialized. Call initialize() first.")
        self.builder.add_aspirate(location, volume, pre_aspirate_volume, post_aspirate_volume,
                                liquid_class, distance_from_well_bottom, 
                                retract_distance_per_microliter, pipette_technique,
                                perform_tip_touch, tip_touch_side, 
                                tip_touch_retract_distance, tip_touch_horizontal_offset)
        logging.info(f"✓ Aspirate {volume}µL from location {location} queued")

    def dispense(self, 
                location: int,
                empty_tips: bool = False,
                volume: float = 0.0,
                blowout_volume: float = 0.0,
                liquid_class: str = '',
                distance_from_well_bottom: float = 2.0,
                retract_distance_per_microliter: float = 0.0,
                pipette_technique: str = '',
                perform_tip_touch: bool = False,
                tip_touch_side: str = 'None',
                tip_touch_retract_distance: float = 0.0,
                tip_touch_horizontal_offset: float = 0.0) -> None:
        """Dispense to location"""
        if not self._initialized:
            raise RuntimeError("Bravo not initialized. Call initialize() first.")
        self.builder.add_dispense(location, empty_tips, volume, blowout_volume,
                                liquid_class, distance_from_well_bottom,
                                retract_distance_per_microliter, pipette_technique,
                                perform_tip_touch, tip_touch_side,
                                tip_touch_retract_distance, tip_touch_horizontal_offset)
        logging.info(f"✓ Dispense {volume}µL to location {location} queued")



    def initialize(self, deck_configuration: Optional[Dict[int, str]] = None) -> None:
        """Initialize Bravo with deck configuration
        
        Args:
            deck_configuration: Dictionary mapping position (1-9) to labware name
        """
        if deck_configuration is None:
            deck_configuration = {}
        
        self.builder.add_subprocess_task(deck_configuration)
        self._initialized = True
        logging.info("✓ Bravo initialization queued")
    
    def mix(self, 
            location: int, 
            volume: float, 
            pre_aspirate_volume: float = 0.0, 
            blowout_volume: float = 0.0,
            liquid_class: str = '', 
            cycles: int = 3,
            retract_distance_per_microliter: float = 0.0,
            pipette_technique: str = '',
            aspirate_distance: float = 2.0, 
            dispense_distance: float = 2.0,
            perform_tip_touch: bool = False,
            tip_touch_side: str = 'None', 
            tip_touch_retract_distance: float = 0.0,
            tip_touch_horizontal_offset: float = 0.0) -> None:
        """
        Mix at location with dual height support
        
        Args:
            location: Location to mix at
            volume: Volume to mix (0 - 250 µL)
            pre_aspirate_volume: Volume to pre-aspirate (µL)
            blowout_volume: Volume to blowout after mixing (µL)
            liquid_class: Liquid class name
            cycles: Number of mix cycles
            retract_distance_per_microliter:  Amount the Z axis retracts per µL aspirated (mm/µL)
            pipette_technique: Pipette technique name
            aspirate_distance: Distance from bottom for aspirate (mm)
            dispense_distance: Distance from bottom for dispense (mm)
            perform_tip_touch: Whether to perform tip touch after mix
            tip_touch_side: Side(s) to perform tip touch on ('None', 'South', 'West', 'North', 'Front', 'East', 'South/North', 'West/East', 'West/East/South/North')
            tip_touch_retract_distance: Distance to retract after tip touch (mm) (-20 to 50)
            tip_touch_horizontal_offset: Horizontal offset for tip touch (mm) (-9 to 5)
       """
        if not self._initialized:
            raise RuntimeError("Bravo not initialized. Call initialize() first.")
        
        assert volume > 0 and volume <= 250, "Volume must be between 0 and 250 µL"
        assert cycles > 0, "Cycles must be greater than 0"
        assert tip_touch_side in ['None', 'South', 'West', 'North', 'Front', 'East', 
                                  'South/North', 'West/East', 'West/East/South/North'], "Invalid tip touch side"
        assert tip_touch_retract_distance >= -20 and tip_touch_retract_distance <= 50, "Tip touch retract distance must be non-negative"
        assert tip_touch_horizontal_offset >= -9 and tip_touch_horizontal_offset <= 5, "Tip touch horizontal offset must be non-negative"
        assert tip_touch_horizontal_offset >= 0, "Tip touch horizontal offset must be non-negative" 

        self.builder.add_mix(location, 
                                volume, 
                                pre_aspirate_volume, 
                                blowout_volume, 
                                liquid_class, 
                                cycles, 
                                retract_distance_per_microliter,
                                pipette_technique, 
                                aspirate_distance, 
                                dispense_distance,
                                perform_tip_touch,
                                tip_touch_side,
                                tip_touch_retract_distance,
                                tip_touch_horizontal_offset)
        logging.info(f"✓ Mix {volume}µL x{cycles} at location {location} queued")
    
    def home(self, axis: str = 'X', force: bool = True) -> None:
        """Home/initialize axes
        
        Args:
            axis: Axis to home - 'X', 'Y', 'Z', 'W', 'G', 'Zg'
            force: Initialize even if already homed
        """
        if not self._initialized:
            raise RuntimeError("Bravo not initialized. Call initialize() first.")
        self.builder.add_initialize_axis(axis, force)
        logging.info(f"✓ Home {axis} axis queued")

    def execute(self, simulate: bool = False, clear_after_execution: bool = True) -> None:
        """Execute all queued commands"""
        if not self.builder.tasks:
            logging.warning("No tasks to execute")
            return
        
        # Generate protocol XML
        xml_content = self.builder.build_xml()
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "outputs"
        )
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        # Save to file
        protocol_path = os.path.join(output_dir, f'bravo_protocol_{int(time.time())}.pro')
        
        try:
            # Write with UTF-8 to handle µ character
            with open(protocol_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            logging.info(f"Executing protocol with {len(self.builder.tasks)} tasks: {protocol_path}")
            
            if simulate or os.name != 'nt':
                logging.info(f"✓ Protocol simulation mode - not executing. See protocol at {protocol_path}")
                return
            
            # Run via VWorks driver
            self.vworks.run_protocol(str(protocol_path))
            
            # Clear tasks after successful execution
            self.builder.tasks = []
            logging.info("✓ Protocol executed successfully")
            
        finally:
            # Clean up
            try:
                if os.path.exists(protocol_path):
                    os.remove(protocol_path)
                    logging.info("✓ Protocol file deleted after execution")
            except Exception as e:
                logging.warning(f"Could not delete protocol file: {e}")
    
    def close(self) -> None:
        """Close driver"""
        logging.info("✓ Bravo driver closed")


# Example usage
if __name__ == "__main__":

    # Device configuration
    device_file = r'/Users/silvioo/Documents/git_projects/galago-tools/tools/bravo/multiple_devices.dev'

    # Create driver
    bravo = BravoVWorksDriver(device_file)

    # Initialize Bravo with deck configuration
    bravo.initialize({
        1: '96 V11 LT250 Tip Box Standard',
        2: '96 V11 LT250 Tip Box Standard',
        3: '96 V11 LT250 Tip Box Standard',
        4: '96 Greiner 655101 PS Clr Rnd Well Flat Btm',  # Source plate 1
        5: '96 Greiner 655101 PS Clr Rnd Well Flat Btm',  # Source plate 2
        6: '96 Greiner 655101 PS Clr Rnd Well Flat Btm',  # Source plate 3
        7: '96 Greiner 655101 PS Clr Rnd Well Flat Btm',  # Destination plate 1
        8: '96 Greiner 655101 PS Clr Rnd Well Flat Btm',  # Destination plate 2
        9: '96 Greiner 655101 PS Clr Rnd Well Flat Btm',  # Destination plate 3
    })

    # Define deck layout
    tip_positions = [1, 2, 3]
    source_positions = [4, 5, 6]
    destination_positions = [7, 8, 9]

    # Transfer parameters
    transfer_volume = 50.0  # µL
    aspirate_height = 2.0   # mm from bottom
    dispense_height = 5.0   # mm from bottom

    # # Iterate through each column
    # for column_idx in range(3):
    #     tip_loc = tip_positions[column_idx]
    #     source_loc = source_positions[column_idx]
    #     dest_loc = destination_positions[column_idx]
        
    #     logging.info(f"--- Processing Column {column_idx + 1} ---")
        
    #     # Pick up tips
    #     bravo.tips_on(tip_loc)
        
    #     # Aspirate from source
    #     bravo.aspirate(
    #         location=source_loc,
    #         volume=transfer_volume,
    #         distance_from_well_bottom=aspirate_height
    #     )
        
    #     # Dispense to destination
    #     bravo.dispense(
    #         location=dest_loc,
    #         volume=transfer_volume,
    #         distance_from_well_bottom=dispense_height
    #     )
        
    #     # Eject tips
    #     bravo.tips_off(tip_loc)

    # # Home the pipette head when done
    bravo.home('X')

    # # Execute the protocol
    bravo.execute(simulate=True, clear_after_execution=False)

    # Close driver
    bravo.close()

    logging.info("✓ Automated transfer complete!")