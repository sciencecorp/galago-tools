from tools.toolbox.db import Db 
from typing import Any, Dict, Optional

db = Db()

def get_inventory(name:str) -> Any:
    response = db.get_by_id_or_name(name, "inventory")
    return response
    
def get_all_inventory(workcell_name: Optional[str] = None) -> Any:
    """
    Get inventory items, optionally filtered by workcell_name.
    If workcell_name is None, attempts to get all inventory items.
    """
    if workcell_name:
        response = db.get_data(f"inventory?workcell_name={workcell_name}")
    else:
        response = db.get_data("inventory?all_workcells=true")
    return response

# Nest functions
def get_nests(workcell_name: str) -> Any:
    response = db.get_data(f"nests?workcell_name={workcell_name}")
    return response

def get_nest(nest_id: int) -> Any:
    response = db.get_by_id_or_name(nest_id, "nests")
    return response

def create_nest(nest_data: Dict[str, Any]) -> Any:
    response = db.post_data(nest_data, "nests")
    return response

def update_nest(nest_id: int, nest_data: Dict[str, Any]) -> Any:
    response = db.update_data(nest_id, nest_data, "nests")
    return response

def delete_nest(nest_id: int) -> Any:
    response = db.delete_data(nest_id, "nests")
    return response

# Plate functions
def get_plates(workcell_name: str) -> Any:
    response = db.get_data(f"plates?workcell={workcell_name}")
    return response

def get_plate(plate_id: int) -> Any:
    response = db.get_by_id_or_name(plate_id, "plates")
    return response

def get_plate_info(plate_id: int) -> Any:
    response = db.get_data(f"plates/{plate_id}/info")
    return response

def create_plate(plate_data: Dict[str, Any]) -> Any:
    response = db.post_data(plate_data, "plates")
    return response

def update_plate(plate_id: int, plate_data: Dict[str, Any]) -> Any:
    response = db.update_data(plate_id, plate_data, "plates")
    return response

def delete_plate(plate_id: int) -> Any:
    response = db.delete_data(plate_id, "plates")
    return response

# Well functions
def get_wells(plate_id: int) -> Any:
    response = db.get_data(f"wells?plate_id={plate_id}")
    return response

# Reagent functions
def get_reagents(plate_id: int) -> Any:
    response = db.get_data(f"reagents?plate_id={plate_id}")
    return response

def get_workcell_reagents(workcell_name: str) -> Any:
    response = db.get_data(f"reagents?workcell_name={workcell_name}")
    return response

def create_reagent(reagent_data: Dict[str, Any]) -> Any:
    response = db.post_data(reagent_data, "reagents")
    return response

def update_reagent(reagent_id: int, reagent_data: Dict[str, Any]) -> Any:
    response = db.update_data(reagent_id, reagent_data, "reagents")
    return response

def delete_reagent(reagent_id: int) -> Any:
    response = db.delete_data(reagent_id, "reagents")
    return response

def get_reagents_by_name_and_quantity(reagent_name: str, quantity: int, workcell_name: str) -> Any:
    """
    Returns an array of reagents with the specified name and quantity from a single plate.
    
    Args:
        reagent_name: The name of the reagent to search for
        quantity: The required quantity of the reagent
        workcell_name: The name of the workcell to search in
        
    Returns:
        A list of matching reagents or raises an exception if none found
    """
    # Get all reagents for the workcell
    all_reagents = get_workcell_reagents(workcell_name)
    
    # Filter reagents by name and quantity
    matching_reagents = [r for r in all_reagents if r.get("name") == reagent_name and r.get("quantity", 0) >= quantity]
    
    if not matching_reagents:
        raise Exception(f"No reagents found with name '{reagent_name}' and quantity {quantity} in workcell '{workcell_name}'")
    
    # Group reagents by plate_id
    reagents_by_plate = {}
    for reagent in matching_reagents:
        plate_id = reagent.get("plate_id")
        if plate_id not in reagents_by_plate:
            reagents_by_plate[plate_id] = []
        reagents_by_plate[plate_id].append(reagent)
    
    # Find the plate with the most matching reagents
    best_plate_id = None
    max_reagents = 0
    for plate_id, reagents in reagents_by_plate.items():
        if len(reagents) > max_reagents:
            max_reagents = len(reagents)
            best_plate_id = plate_id
    
    if best_plate_id is None:
        raise Exception(f"Could not determine a suitable plate for reagent '{reagent_name}' with quantity {quantity}")
    
    return reagents_by_plate[best_plate_id]
 

