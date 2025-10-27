from opentrons import protocol_api
from typing import List
metadata = {"apiLevel": "2.12"}
## FRT_PARAMS_START ###
# The following will be replaced by the actual parameters on the workcell
# during process execution.
global_reagent_index = 0
# params for 384 well plate
# params = {
#     "tiprack_wells": [
#       "F1"
#     ],
#     "reagent_wells": [
#     ["A1","A2"],
#     ["A3","A4"],
#     ["A5","A6"]
#     ],
#   }

params = {
    "tiprack_wells": {"20 ul tips":["F4","G4","H4","A5","B5","C5","D5","E5","F5","G5","H5","A6"],"1000 ul tips":["C3","D3","E3","F3"]},
    "lipoWell": "C12",
    "p3000Well": "D12",
    "dna_wells": ["C10","D10","A11","B11"], 
    "t_wells": ["C1", "B2", "B3", "B4"],
    "plasmid_wells": ["D4"," F5"," F8"," G1"],
    "tipbox_slot": 6,
    "dna_concentration": [1000.0,1000.0,800.0,800.0],
    "DNAPlateType": "96-well deepwell",
    "DNAMass": [1000.0,2500.0,1000.0,1000.0],
}


#type check params 

if not isinstance(params["tiprack_wells"], dict):
    raise Exception("tiprack_wells must be a dict")
if not isinstance(params["lipoWell"], str):
    raise Exception("lipoWell must be a string")
if not isinstance(params["p3000Well"], str):
    raise Exception("p3000Well must be a string")
if not isinstance(params["dna_wells"], list):
    raise Exception("dna_wells must be a list")
if not isinstance(params["t_wells"], list):
    raise Exception("t_wells must be a list")
if not isinstance(params["plasmid_wells"], list):
    raise Exception("plasmid_wells must be a list")
if not isinstance(params["tipbox_slot"], int):
    raise Exception("tipbox_slot must be an int")
if not isinstance(params["lipoWell"], str):
    raise Exception("lipoWell must be a string")
if not isinstance(params["p3000Well"], str):
    raise Exception("p3000Well must be a string")
if not isinstance(params["dna_wells"], list) or not all(isinstance(item, str) for item in params["dna_wells"]):
    raise Exception("dna_wells must be a list of strings")
if not isinstance(params["t_wells"], list) or not all(isinstance(item, str) for item in params["t_wells"]):
    raise Exception("t_wells must be a list of strings")
if not isinstance(params["plasmid_wells"], list) or not all(isinstance(item, str) for item in params["plasmid_wells"]):
    raise Exception("plasmid_wells must be a list of strings")
if not isinstance(params["dna_concentration"], list) or not all(isinstance(item, float) for item in params["dna_concentration"]):
    raise Exception("dna_concentration must be a list of floats")
if not isinstance(params["DNAPlateType"], str):
    raise Exception("DNAPlateType must be a string")
if not isinstance(params["DNAMass"], list) or not all(isinstance(item, float) for item in params["DNAMass"]):
    raise Exception("DNAMass must be a list of floats")



 #print the params to the command line for debugging


### FRT_PARAMS_END ###

# params = {
#     "tiprack_wells": {"20 ul tips":["B1","C1","D1"],"1000 ul tips":["A1"]},
#     "lipoWell": "B1",
#     "p3000Well": "C1",
#     "dna_wells": ["A1",], 
#     "t_wells": ["C1"],
#     "plasmid_wells": ["D1"],
#     "tipbox_slot": 6,
# }

# Get current instrument config = unused reagent well index and unused tip index
PLATE_OFFSET  = 2
tiprack_wells: dict = params["tiprack_wells"]
lipoWell: str = params["lipoWell"]
p3000Well: str = params["p3000Well"]
dna_wells: List[str] = params["dna_wells"]
t_wells: List[str] = params["t_wells"]
plasmid_wells: List[str] = params["plasmid_wells"]
tipbox_slot: int = params["tipbox_slot"]
dna_concentration: List[float] = params["dna_concentration"]
DNAPlateType: str = params["DNAPlateType"]
DNAMass: List[float] = params["DNAMass"]

def run(
    protocol: protocol_api.ProtocolContext,
    tiprack_wells: dict = tiprack_wells,
    dna_wells: List[str] = dna_wells,
    plasmid_wells: List[str] = plasmid_wells,
    dna_concentration: List[float] = dna_concentration,
    DNAPlateType: str = DNAPlateType,
    DNAMass: List[float] = DNAMass,
) -> None:

  tiprack_20 = protocol.load_labware('opentrons_96_filtertiprack_20ul', 3)
  tiprack_20.set_offset(x=-5.00, y=4.50, z=0.00)
  dna_mix_wells = dna_wells
  tiprack_1000 = protocol.load_labware('opentrons_96_filtertiprack_1000ul', 6)
  tiprack_1000.set_offset(x=0.50, y=2, z=0.00)
  
  t_reagent_plate = protocol.load_labware("nest_96_wellplate_2ml_deep", 5)
  t_reagent_plate.set_offset(x=-5.0, y=6.00, z=86)

  if DNAPlateType == "96-well deepwell":
        dna_plate = protocol.load_labware("nest_96_wellplate_2ml_deep", 2)
        dna_plate.set_offset(x=-7.00, y=5, z=62.5)
  elif DNAPlateType == "96-well Twist Plate" or DNAPlateType == "96-Well Twist Plate":
    dna_plate = protocol.load_labware("biorad_96_wellplate_200ul_pcr", 2)
    dna_plate.set_offset(x=-7.00, y=4, z=62.4)
  
    
  p20 = protocol.load_instrument('p20_single_gen2', 'right', tip_racks=[tiprack_20])
  p1000 = protocol.load_instrument('p1000_single_gen2', 'left', tip_racks=[tiprack_1000])
  p20.default_speed = 150
  p20.flow_rate.aspirate = 100
  p20.flow_rate.dispense = 200
  p1000.default_speed = 400 
  tips_20 = tiprack_wells["20 ul tips"]

  #remove spaces from plasmid_wells

  plasmid_wells = [x.strip() for x in plasmid_wells]

# add DNA to each well in t_wells
  dna_vol = [a / b for a, b in zip(DNAMass, dna_concentration)]
  #TODO input: concentration of DNA, calculate vol of dna to add 
  for i in range(0, len(plasmid_wells)):
      starting_tip = tips_20[i]
      next_tip = tiprack_20.next_tip(starting_tip=tiprack_20.wells_by_name()[starting_tip])
      p20.pick_up_tip(next_tip)
      p20.aspirate(dna_vol[i], dna_plate[plasmid_wells[i]])
      p20.move_to(dna_plate[plasmid_wells[i]].top())
      #pause for a few seconds to prevent dripping
      protocol.delay(seconds=3)
      p20.dispense(dna_vol[i], t_reagent_plate[dna_mix_wells[i]])
      p20.mix(1, 20, t_reagent_plate[dna_mix_wells[i]])
      p20.blow_out(t_reagent_plate[dna_mix_wells[i]].bottom(5))
      p20.drop_tip()

      