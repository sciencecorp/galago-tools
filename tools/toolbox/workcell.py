from tools.toolbox.db import Db 
from typing import Any

db = Db()

def get_workcell(id:int) -> Any:
    response = db.get_by_id_or_name(id, "workcells")
    return response
    
def get_all_workcells() -> Any:
    response = db.get_data("workcells")
    return response

