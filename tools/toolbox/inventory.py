from tools.toolbox.db import Db 
from typing import Any, Dict

db = Db()

def get_inventory(id:int) -> Any:
    response = db.get_by_id_or_name(id, "inventory")
    return response
    
def get_all_inventory() -> Any:
    response = db.get_data("inventory")
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
 

