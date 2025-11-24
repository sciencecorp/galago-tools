import logging
import argparse
import threading
from typing import Dict, Any
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.bravo_pb2 import Command, Config
from .driver import BravoVWorksDriver

_thread_local = threading.local()


class BravoServer(ToolServer):
    toolType = "bravo"
    config: Config
    
    def __init__(self) -> None:
        super().__init__()
        self.main_thread_id = threading.get_ident()
        self._initialized = False
        logging.info(f"BravoServer initialized in thread ID: {self.main_thread_id}")
        
    def _configure(self, request: Config) -> None:
        logging.info(f"Configuring Bravo in thread ID: {threading.get_ident()}")
        self.config = request
        logging.info(f"Bravo configuration complete with device file: {request.device_file}")
    
    def _get_thread_driver(self) -> Any:
        """Get or create a driver instance for the current thread"""
        thread_id = threading.get_ident()
        
        if not hasattr(_thread_local, 'driver'):
            logging.info(f"Creating new BravoVWorksDriver in thread ID: {thread_id}")
            _thread_local.driver = BravoVWorksDriver(self.config.device_file)
            logging.info(f"BravoVWorksDriver created for thread ID: {thread_id}")
        
        return _thread_local.driver
    
    def cleanup(self) -> None:
        """Clean up resources properly for all threads"""
        logging.info(f"Cleanup called from thread ID: {threading.get_ident()}")
        
        # Clean up the driver in the current thread if it exists
        if hasattr(_thread_local, 'driver'):
            try:
                logging.info(f"Cleaning up driver for thread ID: {threading.get_ident()}")
                _thread_local.driver.close()
                delattr(_thread_local, 'driver')
            except Exception as e:
                logging.error(f"Error closing driver: {e}")
    
    def ConfigureDeck(self, params: Command.ConfigureDeck) -> None:
        """Initialize Bravo with deck configuration"""
        thread_id = threading.get_ident()
        logging.info(f"ConfigureDeck called from thread ID: {thread_id}")
        
        driver = self._get_thread_driver()
        
        # Convert protobuf Struct to Python dict
        deck_config: Dict[int, str] = {}
        if params.deck_configuration:
            for key, value in params.deck_configuration.items():
                try:
                    position = int(key)
                    labware = str(value)
                    deck_config[position] = labware
                except (ValueError, TypeError) as e:
                    logging.warning(f"Invalid deck configuration entry: {key}={value}, {e}")
        
        driver.initialize(deck_config)
        self._initialized = True
        logging.info(f"Deck configured with {len(deck_config)} positions")
    
    def Home(self, params: Command.Home) -> None:
        """Home/initialize axes"""
        thread_id = threading.get_ident()
        logging.info(f"Home called from thread ID: {thread_id}")
        
        driver = self._get_thread_driver()
        driver.home(axis=params.axis, force=params.force_initialize)
        logging.info(f"Homed axis: {params.axis}")
    
    def Mix(self, params: Command.Mix) -> None:
        """Mix at location"""
        thread_id = threading.get_ident()
        logging.info(f"Mix called from thread ID: {thread_id}")
        
        driver = self._get_thread_driver()
        driver.mix(
            location=params.location,
            volume=params.volume,
            pre_aspirate_volume=params.pre_aspirate_volume,
            blowout_volume=params.blow_out_volume,
            liquid_class=params.liquid_class,
            cycles=params.cycles,
            retract_distance_per_microliter=params.retract_distance_per_microliter,
            pipette_technique=params.pipette_technique,
            aspirate_distance=params.aspirate_distance,
            dispense_distance=params.dispense_distance,
            perform_tip_touch=params.perform_tip_touch,
            tip_touch_side=params.tip_touch_side,
            tip_touch_retract_distance=params.tip_touch_retract_distance,
            tip_touch_horizontal_offset=params.tip_touch_horizonal_offset
        )
        logging.info(f"Mix queued: {params.volume}µL x{params.cycles} at location {params.location}")
    
    def Aspirate(self, params: Command.Aspirate) -> None:
        """Aspirate from location"""
        thread_id = threading.get_ident()
        logging.info(f"Aspirate called from thread ID: {thread_id}")
        
        driver = self._get_thread_driver()
        driver.aspirate(
            location=params.location,
            volume=params.volume,
            pre_aspirate_volume=params.pre_aspirate_volume,
            post_aspirate_volume=params.post_aspirate_volume,
            liquid_class=params.liquid_class,
            distance_from_well_bottom=params.distance_from_well_bottom,
            retract_distance_per_microliter=params.retract_distance_per_microliter,
            pipette_technique=params.pipette_technique,
            perform_tip_touch=params.perform_tip_touch,
            tip_touch_side=params.tip_touch_side,
            tip_touch_retract_distance=params.tip_touch_retract_distance,
            tip_touch_horizontal_offset=params.tip_touch_horizonal_offset
        )
        logging.info(f"Aspirate queued: {params.volume}µL from location {params.location}")
    
    def Dispense(self, params: Command.Dispense) -> None:
        """Dispense to location"""
        thread_id = threading.get_ident()
        logging.info(f"Dispense called from thread ID: {thread_id}")
        
        driver = self._get_thread_driver()
        driver.dispense(
            location=params.location,
            empty_tips=params.empty_tips,
            volume=params.volume,
            blowout_volume=params.blow_out_volume,
            liquid_class=params.liquid_class,
            distance_from_well_bottom=params.distance_from_well_bottom,
            retract_distance_per_microliter=params.retract_distance_per_microliter,
            pipette_technique=params.pipette_technique,
            perform_tip_touch=params.perform_tip_touch,
            tip_touch_side=params.tip_touch_side,
            tip_touch_retract_distance=params.tip_touch_retract_distance,
            tip_touch_horizontal_offset=params.tip_touch_horizonal_offset
        )
        logging.info(f"Dispense queued: {params.volume}µL to location {params.location}")
    
    def TipsOn(self, params: Command.TipsOn) -> None:
        """Pick up tips at location"""
        thread_id = threading.get_ident()
        logging.info(f"TipsOn called from thread ID: {thread_id}")
        
        driver = self._get_thread_driver()
        driver.tips_on(params.plate_location)
        logging.info(f"TipsOn queued at location {params.plate_location}")
    
    def TipsOff(self, params: Command.TipsOff) -> None:
        """Eject tips at location"""
        thread_id = threading.get_ident()
        logging.info(f"TipsOff called from thread ID: {thread_id}")
        
        driver = self._get_thread_driver()
        driver.tips_off(params.plate_location)
        logging.info(f"TipsOff queued at location {params.plate_location}")
    
    def MoveToLocation(self, params: Command.MoveToLocation) -> None:
        """Move to specified location"""
        thread_id = threading.get_ident()
        logging.info(f"MoveToLocation called from thread ID: {thread_id}")
        
        driver = self._get_thread_driver()
        driver.move_to_location(params.plate_location)
        logging.info(f"MoveToLocation queued to location {params.plate_location}")
    
    def ShowDiagnostics(self, params: Command.ShowDiagnostics) -> None:
        """Show diagnostics information"""
        thread_id = threading.get_ident()
        logging.info(f"ShowDiagnostics called from thread ID: {thread_id}")
        
        driver = self._get_thread_driver()
        logging.info(f"Device file: {self.config.device_file}")
        logging.info(f"Device name: {driver.builder.device_name}")
        logging.info(f"Initialized: {driver._initialized}")
        logging.info(f"Queued tasks: {len(driver.builder.tasks)}")
    
    def EstimateConfigureDeck(self, params: Command.ConfigureDeck) -> int:
        """Estimate time for ConfigureDeck in seconds"""
        return 10
    
    def EstimateHome(self, params: Command.Home) -> int:
        """Estimate time for Home in seconds"""
        return 15 if 'Z' in params.axis.upper() else 5
    
    def EstimateMix(self, params: Command.Mix) -> int:
        """Estimate time for Mix in seconds"""
        return 5
    
    def EstimateAspirate(self, params: Command.Aspirate) -> int:
        """Estimate time for Aspirate in seconds"""
        return 5
    
    def EstimateDispense(self, params: Command.Dispense) -> int:
        """Estimate time for Dispense in seconds"""
        return 5
    
    def EstimateTipsOn(self, params: Command.TipsOn) -> int:
        """Estimate time for TipsOn in seconds"""
        return 5
    
    def EstimateTipsOff(self, params: Command.TipsOff) -> int:
        """Estimate time for TipsOff in seconds"""
        return 5
    
    def EstimateMoveToLocation(self, params: Command.MoveToLocation) -> int:
        """Estimate time for MoveToLocation in seconds"""
        return 26
    
    def EstimateShowDiagnostics(self, params: Command.ShowDiagnostics) -> int:
        """Estimate time for ShowDiagnostics in seconds"""
        return 1


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True, help='Port for the gRPC server')
    args = parser.parse_args()
    
    if not args.port:
        raise RuntimeWarning("Port must be provided...")
    
    logging.info("Starting Bravo gRPC server...")
    serve(BravoServer(), str(args.port))