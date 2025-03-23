from tools.toolbox.db import Db
from typing import Any, Dict

db = Db()

def get_all_logs() -> Any:
    """Get all logs from the database."""
    response = db.get_data("logs")
    return response

def get_paginated_logs(skip: int, limit: int, descending: bool) -> Any:
    """Get paginated logs from the database.
    
    Args:
        skip: Number of logs to skip
        limit: Maximum number of logs to return
        descending: Whether to sort in descending order
    """
    response = db.get_data(f"logs?skip={skip}&limit={limit}&descending={descending}")
    return response

def clear_all_logs() -> Any:
    """Clear all logs from the database."""
    # The delete_data method typically requires an ID, but in this case,
    # we're deleting all logs, so we'll use a special endpoint
    response = db.delete_data("", "logs")
    return response

def add_log(log_data: Dict[str, Any]) -> Any:
    """Add a new log to the database.
    
    Args:
        log_data: Dictionary containing log information
    """
    response = db.post_data(log_data, "logs")
    return response
