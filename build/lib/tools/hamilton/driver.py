#from tools.base_server import ABCToolDriver
import os
import time
import subprocess
import logging 
from typing import Optional 
from os.path import join
from tools.base_server import ABCToolDriver

RUN_CONTROL_SDK = "C:\\Program Files (x86)\\Hamilton\\Bin\\HxRun.exe"
DIR_NAME = os.path.dirname(os.path.abspath(__file__))
VENUS_LOG = join(DIR_NAME, "venus.log")


class HamiltonDriver(ABCToolDriver):

    def __init__(self)-> None:
        if not os.path.exists(RUN_CONTROL_SDK):
            raise ImportError(f"Failed to find {RUN_CONTROL_SDK}. Make sure that the path is correct.")
        self.protocol_name : Optional[str] = None
        self.live : bool  = False
        self.hamilton_process : Optional[subprocess.Popen] = None
        self.kill_processes("HsRun.exe")

    def remove_venus_log(self) -> None:
        try:
            if os.path.exists(VENUS_LOG):
                os.remove(VENUS_LOG)
        except Exception as ex:
            raise RuntimeError(ex)
        return None
    
    def load_and_run_protocol(self, protocol_name: str, close_on_end:bool =True)-> None:
        try:
            self.kill_processes("HxRun.exe",False)
            self.remove_venus_log()
            cmd  = [RUN_CONTROL_SDK, protocol_name, "-r"]
            if close_on_end:
                cmd.append("-t")
            self.hamilton_process = subprocess.Popen(cmd,stdout=open("venus.log",'a'), stderr=subprocess.STDOUT,  universal_newlines=True)
        except subprocess.CalledProcessError as ex:
            raise RuntimeError(f"Failed to run {protocol_name}'. Error Message: {str(ex)}")
        return None 
    
    def wait_for_protocol(self, timeout:int=500) -> None:
        start_time = time.time()
        logging.info(f"Run protocol started at {start_time}")
        seconds_spent_waiting = 0 
        while True:
            seconds_spent_waiting = int(time.time() - start_time)
            if self.hamilton_process is None:
                break
            status = self.hamilton_process.poll()
            if status is not None:
                break
            if timeout and seconds_spent_waiting > timeout:
                raise Exception("Run protocol has timed out. Please reset VWorks and restart the driver.")
            if os.path.exists(VENUS_LOG):
                try:
                    with open(join(DIR_NAME, "venus.log")) as file:
                        lines = file.readlines()
                        if len(lines) > 0:
                            raise RuntimeError(f"Encountered a run error {','.join(lines)}")
                except Exception as e:
                    raise RuntimeError(f"Encounter a runtime error. Error={e}")
            time.sleep(1)  # Add a small delay to avoid busy-waiting
        logging.info(f"Run protocol completed after {seconds_spent_waiting} seconds")
        return None 
    
    def load_protocol(self, protocol_name: str) -> None:
        if not os.path.exists(protocol_name):
            raise Exception(f"Protocol {protocol_name} not found.")
        self.kill_processes("HsRun.exe",False)
        self.remove_venus_log()
        cmd  = [RUN_CONTROL_SDK, protocol_name]
        try:
            self.hamilton_process = subprocess.Popen(cmd,stdout=open("venus.log",'a'), stderr=subprocess.STDOUT,  universal_newlines=True)
        except Exception as e:
            raise RuntimeError(f"Failed to load protocol {protocol_name}.Reason={e}")
        self.protocol_name = protocol_name

    def run_protocol(self, protocol_name:str) -> None:
        if not os.path.exists(protocol_name):
            raise Exception(f"Protocol {protocol_name} not found.")
        self.load_and_run_protocol(protocol_name)
        self.wait_for_protocol()
        return None
