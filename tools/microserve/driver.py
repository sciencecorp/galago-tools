from tools.comms.tcpip import TcpIp
from tools.base_server import ABCToolDriver
import time 
import logging 
from typing import Optional 

COMMANDS = {
    "home":"h",
    "load":"l",
    "unload":"u",
    "retract":"rt",
    "abort":"a",
    "scan":"bs",
    "set_plate_height":"sph",
    "set_plate_dimensions":"spd",
    "set_plate_thickness":"spt",
    # "status":"s", #Do not use this command for rapid polling bc it communicates with the aplifiers within the machine.
    "varstatus":"vs", #this command is appropiate for use withing driver. 
    "spin":"sp",
    "manual":"m", #set to manual mode. ,
    "get_dimensions":"dimstatus",
    "clear_error":"cba"
}
class MicroServeDriver(ABCToolDriver):
    toolType = "microserve"
    
    def __init__(self, ip:str, port: int) -> None:
        self.tcp : Optional[TcpIp] = None
        self.blocking :bool = True
        self.port : int = port
        self.ip : str = ip
        self.error : Optional[str] = None
    
    def connect(self) -> None:
        logging.info(f"Connecting to microserve at ip: {self.ip} and port {self.port}")
        try:
            self.tcp = TcpIp(self.ip, self.port)
            self.tcp.connect()
        except Exception as e:
            logging.info(f"Failed to connect to MicroServe: {e}")
            self.error = str(e)
            raise ValueError(f"Failed to connect to MicroServe: {e}")

    def get_status(self) -> str:
        return  self.send_command(COMMANDS["varstatus"])
    
    def is_homed(self) -> bool:
        logging.info("Checking if microserve is homed")
        response = self.get_status()
        logging.info(f"Home status {response}")
        time.sleep(0.1)
        if "OK! status homed" in response:
            logging.info("Microserve is already homed")
            return True
        else:
            logging.info("Microserve is not homed")
            return False

    def home(self, skip_if_homed:bool=False) -> None:
        if not skip_if_homed:
            self.send_command(COMMANDS["home"])
        else:
            if not self.is_homed():
                self.send_command(COMMANDS["home"])
            else:
                logging.info("Skipping homing")

    def get_dimensions(self) -> None:
        self.send_command(COMMANDS["get_dimensions"])

    def abort(self) -> None:
        self.send_command(COMMANDS["abort"])

    def retract(self) -> None:
        self.send_command(COMMANDS["retract"])

    #Retracts the spatula if necessary, spins to stack id and raises spatula for plate to be placed
    def load(self, stack_id:int, plate_height:float, plate_thickness:float, plate_stack_height:float) -> None:
        if stack_id > 16:
            raise RuntimeError("Invalid Stack Id. Range must be 0-16")
        self.home(True)
        stack_id -= 1
        self.set_plate_dimensions(plate_stack_height, plate_thickness, plate_height)
        try:
            self.send_command(f"l {stack_id}")
        except Exception:
            raise RuntimeError(f"Failed to Load plate into {stack_id}")
        self.set_plate_dimensions(plate_stack_height, plate_thickness, plate_height)
        print(f"Loaded plate into stack {stack_id}")

    #Presents the plate to be unloaded by the robot arm
    def unload(self, stack_id:int, plate_height:float, plate_thickness:float, plate_stack_height:float) -> None:
        if stack_id > 16:
            raise RuntimeError("Invalid Stack Id. Range must be 0-16")
        self.home(True)
        stack_id -= 1
        self.set_plate_dimensions(plate_stack_height, plate_thickness, plate_height)
        try:
            self.send_command(f"u {stack_id}")
        except Exception:
            raise RuntimeError(f"Failed to unload plate from {stack_id}")
        self.set_plate_dimensions(plate_stack_height, plate_thickness, plate_height)
        print(f"Unloaded plate from stack {stack_id}")

    def go_to(self, stack_id:int) -> None:
        if stack_id > 16:
            raise RuntimeError("Invalid Stack Id. Range must be 0-16")
        stack_id -= 1
        logging.info(f"Spinning to stack {stack_id}")
        cmd = COMMANDS["spin"]
        self.send_command(f"{cmd} {stack_id}", 30000)

    def set_plate_dimensions(self, plate_height:float, stack_height:float, plate_thickness:float) -> None:
        logging.info("Setting microserve plate dimensions")
        logging.info(f"Plate height= {plate_height}")
        logging.info(f"Stacked height= {stack_height}")
        logging.info(f"Well Height= {plate_thickness}")
        cmd = COMMANDS["set_plate_dimensions"]
        self.send_command(f"{cmd} {plate_height*1000} {stack_height*1000} {plate_thickness*1000}", 5000)

    def set_to_manual(self) -> None:
        self.send_command(COMMANDS["manual"])

    def disconnect(self) -> None:
        if self.tcp:
            self.tcp.disconnect()

    def send_command(self, message:str, timeout:int=30000) -> str:
        if not self.tcp:
            raise ConnectionError("Not connected to any server.")
        self.tcp.clear_buffer()
        result = self.tcp.send_command(message)
        logging.info(f"Acknowledgement response is {result}")
        if "ACK!" not in result:
            raise ValueError(f"Invalid response: {result}")
        
        wait_response = self.wait_for_command(timeout)
        return wait_response

    def wait_for_command(self, timeout:int) -> str:
        response = ""
        if self.blocking and self.tcp:
            response = self.tcp.read_response(timeout=timeout)
            if response.lower().startswith(("error", "aborted")):
                raise ValueError(f"Failed to complete command. Error: {response}")
        return response
    