from tools.toolbox.db import Db
from typing import Any, Dict, Union

db = Db()

def get_all_labware() -> Any:
    """Get all labware from the database."""
    response = db.get_data("labware")
    return response

def get_labware(labware_id: Union[int, str]) -> Any:
    """Get a specific labware by ID or name."""
    response = db.get_by_id_or_name(labware_id, "labware")
    return response

def add_labware(labware_data: Dict[str, Any]) -> Any:
    """Add a new labware to the database."""
    response = db.post_data(labware_data, "labware")
    return response

def edit_labware(labware_id: int, labware_data: Dict[str, Any]) -> Any:
    """Edit an existing labware in the database."""
    response = db.update_data(labware_id, labware_data, "labware")
    return response

def delete_labware(labware_id: int) -> Any:
    """Delete a labware from the database."""
    response = db.delete_data(labware_id, "labware")
    return response