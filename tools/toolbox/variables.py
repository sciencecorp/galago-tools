import typing as t
from tools.toolbox.db import Db 
from typing import Any

db = Db()

def get_variable(name:str) -> Any:
    response = db.get_by_id_or_name(name, "variables")
    return response
    
def get_all_variables() -> Any:
    response = db.get_data("variables")
    return response

def create_variable(data:dict) -> Any:
    response = db.post_data(data, "variables")
    return response

def update_variable(name:str, new_value:t.Union[str,int,bool]) -> Any:
    variable = {"value": new_value}
    response = db.update_data(name, variable, "variables")
    return response

def delete_variable(name:str) -> Any:
    response = db.delete_data(name, "variables")
    return response
