import logging
import argparse
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.bravo_pb2 import Command, Config
from .driver import BravoDriver


class BravoServer(ToolServer):
    toolType = "bravo"
    config : Config
    
    def __init__(self) -> None:
        super().__init__()
        self.driver : BravoDriver 
        
    def _configure(self, config: Config) -> None:
        self.config = config
        if self.driver:
            self.driver.close()
        self.driver = BravoDriver()
        profile = config.profile 
        if not profile:
            raise ValueError("Profile must be specified in configuration")
        self.driver.initialize(profile)
    
    def Initialize(self, params: Command.Initialize) -> None:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        self.driver.initialize(params.profile)
    
    def Close(self, params: Command.Close) -> None:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        self.driver.close()
    
    def HomeW(self, params: Command.HomeW) -> None:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        self.driver.home_w()
    
    def HomeXYZ(self, params: Command.HomeXYZ) -> None:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        self.driver.home_xyz()
    
    def Mix(self, params: Command.Mix) -> None:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        self.driver.mix(
            volume=params.volume,
            pre_aspirate_volume=params.pre_aspirate_volume,
            blow_out_volume=params.blow_out_volume,
            cycles=params.cycles,
            plate_location=params.plate_location,
            distance_from_well_bottom=params.distance_from_well_bottom,
            retract_distance_per_microliter=params.retract_distance_per_microliter
        )
    
    def Wash(self, params: Command.Wash) -> None:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        self.driver.wash(
            volume=params.volume,
            empty_tips=params.empty_tips,
            pre_aspirate_volume=params.pre_aspirate_volume,
            blow_out_volume=params.blow_out_volume,
            cycles=params.cycles,
            plate_location=params.plate_location,
            distance_from_well_bottom=params.distance_from_well_bottom,
            retract_distance_per_microliter=params.retract_distance_per_microliter,
            pump_in_flow_speed=params.pump_in_flow_speed,
            pump_out_flow_speed=params.pump_out_flow_speed
        )
    
    def Aspirate(self, params: Command.Aspirate) -> None:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        
        # Handle optional parameters
        kwargs = {
            'volume': params.volume,
            'plate_location': params.plate_location
        }
        
        if params.HasField('distance_from_well_bottom'):
            kwargs['distance_from_well_bottom'] = params.distance_from_well_bottom
        if params.HasField('pre_aspirate_volume'):
            kwargs['pre_aspirate_volume'] = params.pre_aspirate_volume
        if params.HasField('post_aspirate_volume'):
            kwargs['post_aspirate_volume'] = params.post_aspirate_volume
        if params.HasField('retract_distance_per_microliter'):
            kwargs['retract_distance_per_microliter'] = params.retract_distance_per_microliter
        
        self.driver.aspirate(**kwargs)
    
    def Dispense(self, params: Command.Dispense) -> None:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        
        # Handle optional parameters
        kwargs = {
            'volume': params.volume,
            'empty_tips': params.empty_tips,
            'blow_out_volume': params.blow_out_volume,
            'plate_location': params.plate_location
        }
        
        if params.HasField('distance_from_well_bottom'):
            kwargs['distance_from_well_bottom'] = params.distance_from_well_bottom
        if params.HasField('retract_distance_per_microliter'):
            kwargs['retract_distance_per_microliter'] = params.retract_distance_per_microliter
        
        self.driver.dispense(**kwargs)
    
    def TipsOn(self, params: Command.TipsOn) -> None:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        self.driver.tips_on(params.plate_location)
    
    def TipsOff(self, params: Command.TipsOff) -> None:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        self.driver.tips_off(params.plate_location)
    
    def MoveToLocation(self, params: Command.MoveToLocation) -> None:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        
        only_z = params.only_z if params.HasField('only_z') else False
        self.driver.move_to_location(params.plate_location, only_z)
    
    def SetLabwareAtLocation(self, params: Command.SetLabwareAtLocation) -> None:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        self.driver.set_labware_at_location(params.plate_location, params.labware_type)
    
    def SetLiquidClass(self, params: Command.SetLiquidClass) -> None:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        self.driver.set_liquid_class(params.liquid_class)
    
    def PickAndPlace(self, params: Command.PickAndPlace) -> None:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        self.driver.pick_and_place(
            source_location=params.source_location,
            dest_location=params.dest_location,
            gripper_offset=params.gripper_offset,
            labware_thickness=params.labware_thickness
        )
    
    def GetDeviceConfiguration(self, params: Command.GetDeviceConfiguration) -> str:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        return self.driver.get_device_configuration()
    
    def GetFirmwareVersion(self, params: Command.GetFirmwareVersion) -> str:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        return self.driver.get_firmware_version()
    
    def EnumerateProfiles(self, params: Command.EnumerateProfiles) -> list[str]:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        return self.driver.enumerate_profiles()
    
    def ShowDiagnostics(self, params: Command.ShowDiagnostics) -> None:
        if not self.driver:
            raise RuntimeError("Driver not configured")
        self.driver.show_diagnostics()
    
    # ==================== Estimate Methods ====================
    
    def EstimateInitialize(self, params: Command.Initialize) -> int:
        return 5  # ~5 seconds to initialize
    
    def EstimateClose(self, params: Command.Close) -> int:
        return 1
    
    def EstimateHomeW(self, params: Command.HomeW) -> int:
        return 10  # Homing can take ~10 seconds
    
    def EstimateHomeXYZ(self, params: Command.HomeXYZ) -> int:
        return 15  # XYZ homing takes longer
    
    def EstimateMix(self, params: Command.Mix) -> int:
        # Estimate based on cycles (rough approximation)
        return max(5, params.cycles * 2)
    
    def EstimateWash(self, params: Command.Wash) -> int:
        # Estimate based on cycles
        return max(5, params.cycles * 3)
    
    def EstimateAspirate(self, params: Command.Aspirate) -> int:
        return 3
    
    def EstimateDispense(self, params: Command.Dispense) -> int:
        return 3
    
    def EstimateTipsOn(self, params: Command.TipsOn) -> int:
        return 2
    
    def EstimateTipsOff(self, params: Command.TipsOff) -> int:
        return 2
    
    def EstimateMoveToLocation(self, params: Command.MoveToLocation) -> int:
        return 2
    
    def EstimateSetLabwareAtLocation(self, params: Command.SetLabwareAtLocation) -> int:
        return 1
    
    def EstimateSetLiquidClass(self, params: Command.SetLiquidClass) -> int:
        return 1
    
    def EstimatePickAndPlace(self, params: Command.PickAndPlace) -> int:
        return 10  # Pick and place operations are slower
    
    def EstimateGetDeviceConfiguration(self, params: Command.GetDeviceConfiguration) -> int:
        return 1
    
    def EstimateGetFirmwareVersion(self, params: Command.GetFirmwareVersion) -> int:
        return 1
    
    def EstimateEnumerateProfiles(self, params: Command.EnumerateProfiles) -> int:
        return 1
    
    def EstimateShowDiagnostics(self, params: Command.ShowDiagnostics) -> int:
        return 1


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True, help='Port number for gRPC server')
    args = parser.parse_args()
    
    logging.info("Starting Bravo gRPC server...")
    serve(BravoServer(), str(args.port))