from tools.toolbox.db import Db
from typing import Any, Dict, Union

db = Db()

def get_all_protocols() -> Any:
    """Get all protocols from the database."""
    response = db.get_data("protocols")
    return response

def get_protocols_by_workcell(workcell_name: str) -> Any:
    """Get all protocols for a specific workcell."""
    response = db.get_data(f"protocols?workcell_name={workcell_name}")
    return response

def get_protocol(protocol_id: Union[int, str]) -> Any:
    """Get a specific protocol by ID."""
    response = db.get_by_id_or_name(protocol_id, "protocols")
    return response

def create_protocol(protocol_data: Dict[str, Any]) -> Any:
    """Create a new protocol in the database.
    
    Args:
        protocol_data: Dictionary containing protocol information including:
            - name: Protocol name
            - category: Protocol category
            - workcell_id: ID of the associated workcell
            - description: Optional description
            - icon: Optional icon
            - params: Parameters for the protocol
            - commands: List of commands for the protocol
            - version: Optional version number (defaults to 1)
            - is_active: Optional active status (defaults to True)
    """
    # Set default values if not provided
    if "version" not in protocol_data:
        protocol_data["version"] = 1
    if "is_active" not in protocol_data:
        protocol_data["is_active"] = True
    if "params" not in protocol_data:
        protocol_data["params"] = {}
    if "commands" not in protocol_data:
        protocol_data["commands"] = []
        
    response = db.post_data(protocol_data, "protocols")
    return response

def update_protocol(protocol_id: int, protocol_data: Dict[str, Any]) -> Any:
    """Update an existing protocol in the database."""
    response = db.update_data(protocol_id, protocol_data, "protocols")
    return response

def delete_protocol(protocol_id: int) -> Any:
    """Delete a protocol from the database."""
    response = db.delete_data(protocol_id, "protocols")
    return response
