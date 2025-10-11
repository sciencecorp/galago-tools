from datetime import datetime
import os
import logging
from enum import Enum 
from typing import Optional, Any
import sys 
import socket 
import subprocess 

class LogType(Enum):
    ERROR = "ERROR",
    WARNING = "WARNING",
    DEBUG = "DEBUG",
    INFO = "INFO",
    PLATE_MOVE = "PLATE_MOVE",
    RUN_START = "RUN_START",
    RUN_END = "RUN_END",
    PLATE_READ = "PLATE_READ",

def get_local_ip() -> Any:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1" # Default local IP
    finally:
        s.close()
    return local_ip

def get_shell_command(tool_type:str, port:int) -> list:
    return [sys.executable, '-m', f'tools.{tool_type}.server', f'--port={port}']

def write_trace_log(log_path:Optional[str], log_type:LogType, tool:str,value:str) -> None:

    if not log_path:
        logging.warning("Log folder not configured")
    if log_path is None:
        return
    if not os.path.exists(log_path):
        try:
            os.makedirs(log_path)
        except Exception as e:
            logging.warning(f"Failed to create log folder. {e}")
            return
    file_folder= os.path.join(log_path, datetime.today().strftime('%Y-%m-%d'))
    if(os.path.exists(file_folder) is False):
        logging.debug("folder does not exist. creating folder")
        os.mkdir(file_folder)

    trace_file = os.path.join(file_folder, "trace_log.txt")
    error_file = os.path.join(file_folder, "error_log.txt")

    try:
        if os.path.exists(trace_file) is False:
            with open(trace_file, 'w+') as f:
                f.write('Time,Tool,Value\n')
        if(log_type == LogType.ERROR):
            if os.path.exists(error_file) is False:
                with open(error_file, 'w+') as f:
                    f.write('Time,Tool,Error\n')
    except Exception as e:
        logging.debug(e)
        return
    try:
        with open(trace_file, 'a') as f:
            f.write(str(datetime.today())+","+str(log_type.name)+","+tool+","+value+"\n")
        if log_type == LogType.ERROR:
            with open(error_file, 'a') as f:
                 f.write(str(datetime.today())+","+str(log_type.name)+","+tool+","+value+"\n")
    except Exception as e:
        logging.debug(e)
        return


        
def check_opentrons_installation() -> bool:
    """
    Check if the opentrons module is properly installed.
    
    Returns:
        bool: True if opentrons is installed and opentrons_simulate is available
    """
    try:
        # Check if we can import the opentrons module
        import opentrons
        
        # Check if opentrons_simulate command is available
        command = ["opentrons_simulate.exe"] if sys.platform == "win32" else ["opentrons_simulate"]
        result = subprocess.run(command + ["--help"], 
                              capture_output=True, 
                              timeout=10)
        return result.returncode == 0
        
    except (ImportError, subprocess.TimeoutExpired, FileNotFoundError):
        return False