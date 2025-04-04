import os
from os.path import  dirname
from pydantic import BaseModel
from typing import Optional, Any
from datetime import date , time 
import logging 
import typing as t
from tools.toolbox.workcell import get_all_workcells
from tools.toolbox.db import Db

ROOT_DIRECTORY = dirname(dirname(os.path.realpath(__file__)))

db = Db()

class Tool(BaseModel):
    id: int
    name :str 
    type: str 
    port: int

class WorkcellConfig(BaseModel):
    id:int = 0
    name: str = "workcell_1"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    tools: list[Tool] = []

class AppConfig(BaseModel):
    workcell:str
    data_folder:Optional[str]
    host_ip: Optional[str] 
    redis_ip: Optional[str] 
    enable_slack_errors: bool 
    slack_bot_tocken: Optional[str]
    slack_workcell_channel: Optional[str]
    slack_error_channel: Optional[str]
    slack_admins_ids: Optional[list[str]]


def get_workcell(id:int) -> Any:
    response = db.get_by_id_or_name(id, "workcells")
    return response

def get_selected_workcell() -> Any:
    workcell = db.get_data("settings/workcell").get("value")
    return workcell

class Config():
    def __init__(self) -> None:
        self.workcell_config : Optional[WorkcellConfig] = None
        self.workcell_config_file  : str = ""

    def serialize(self, obj:t.Any) -> t.Any:
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, date):
            serial = obj.isoformat()
            return serial

        if isinstance(obj, time):
            serial = obj.isoformat()
            return serial
        return obj.__dict__
    
    def load_workcell_config(self)-> None:
        #Ping the database to check if connection is established
        workcells = None
        selected_workcell = None
        db_is_up = db.ping(1)
        if not db_is_up:
            logging.error("Can't establish connection to galago api.")
            logging.warning("Galago api container might be down. "
                            "No instrument tools will be launched.")
            self.workcell_config = WorkcellConfig()
            return None
        else:
            selected_workcell = get_selected_workcell()
            workcells = get_all_workcells()
            if workcells is None or selected_workcell is None:
                logging.error("No workcells or tools found in the database")
                self.workcell_config = WorkcellConfig()
                return None
            selected_workcell_config = [workcell for workcell 
                                        in workcells if 
                                        workcell.get("name") == selected_workcell][0]
            if selected_workcell:
                self.workcell_config = WorkcellConfig.parse_obj(selected_workcell_config)
        return None
    