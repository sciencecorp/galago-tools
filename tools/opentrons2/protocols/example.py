from opentrons import protocol_api
from typing import List
import ast
metadata = {"apiLevel": "2.12"}



## FRT_PARAMS_START ###
# The following will be replaced by the actual parameters on the workcell
# during process execution.


global_reagent_index = 0

params = {
"plate_type": "6 well",
    "percent_change": 100,
    "tiprack_wells": [
      "G12"
    ],
    "tipbox_slot": 8,
    "reagent_wells": [
      "A10",
      "B10"
    ],
    "well_array_to_process": [
      0
    ],
    "new_tip": "True"
  }

#type check params 
if not isinstance(params["tiprack_wells"], list) or not all(isinstance(item, str) for item in params["tiprack_wells"]):
    raise Exception("tiprack_wells must be a list of strings")
if not isinstance(params["tipbox_slot"], int):
    raise Exception("tipbox_slot must be an int")
if not isinstance(params["reagent_wells"], list) or not all(isinstance(item, str) for item in params["reagent_wells"]):
    raise Exception("reagent_wells must be a list of strings")
if not isinstance(params["plate_type"], str):
    raise Exception("plate_type must be a string")
if not isinstance(params["percent_change"], int):
    raise Exception("percent_change must be an int")
if not isinstance(params["well_array_to_process"], list) or not all(isinstance(item, int) for item in params["well_array_to_process"]):
    raise Exception("well_array_to_process must be a list of ints")
if not isinstance(ast.literal_eval(str(params["new_tip"])), bool):
    raise Exception("new_tip must be a boolean")
 #print the params to the command line for debugging
### FRT_PARAMS_END ###

PipetteType = protocol_api.instrument_context.InstrumentContext
TiprackType = protocol_api.labware.Labware
PlateType = protocol_api.labware.Labware
wastePlateType = protocol_api.labware.Labware
ReagentPlateType = protocol_api.labware.Labware
protocolType = protocol_api.protocol_context.ProtocolContext

# Get current instrument config = unused reagent well index and unused tip index
PLATE_OFFSET  = 2
tiprack_wells: List[str] = params["tiprack_wells"]
tipbox_slot: int = params["tipbox_slot"]
reagent_wells: List[str] = params["reagent_wells"]
well_array_to_process: List[int] = params["well_array_to_process"]
plate_type: str = params["plate_type"]
waste_plate_index: int = 0
percent_change: int = params["percent_change"]
new_tip: bool = ast.literal_eval(str(params["new_tip"]))
print("new_tip: ", new_tip)

def run(
    protocol: protocol_api.ProtocolContext,
    plate_type: str = plate_type,
    reagent_wells: List[str] = reagent_wells,
    tiprack_wells: List[str] = tiprack_wells,
    tipbox_slot: int = tipbox_slot,
    well_array_to_process: List[int] = well_array_to_process,
    percent_change: int = percent_change,
    new_tip: bool = new_tip
) -> None:
    # Initialize Labware and Pipettes

    reagent_plate = protocol.load_labware("nest_96_wellplate_2ml_deep", 2)
    reagent_plate.set_offset(x=0.00, y=-1.0, z=1)

    tipbox = protocol.load_labware("opentrons_96_tiprack_300ul", tipbox_slot)

    pipette = protocol.load_instrument("p300_single", "left")

    pipette.pick_up_tip(tipbox.wells()[0])
    pipette.drop_tip()

    protocol.comment("Protocol complete!")