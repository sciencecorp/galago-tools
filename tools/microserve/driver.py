from tools.comms.tcpip import TcpIp
from tools.base_server import ABCToolDriver
import time 

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
    "status":"s", #Do not use this command for rapid polling bc it communicates with the aplifiers within the machine.
    "varstatus":"vs", #this command is appropiate for use withing driver. 
    "spin":"sp",
    "manual":"m", #set to manual mode. ,
    "get_dimensions":"dimstatus"
}
class MicroServeDriver(ABCToolDriver):
    toolType = "microserve"
    
    def __init__(self, ip:str, port: int= 1000) -> None:
        self.tcp = None
        self.blocking = True
        self.port = port
        self.ip = ip
    
    def connect(self, ip, port) -> None:
        try:
            self.tcp = TcpIp(ip, port)
            self.tcp.connect()
        except Exception as e:
            raise ValueError(f"Failed to connect to MicroServe: {e}")

    def is_homed(self) -> bool:
        response = self.send_command(COMMANDS["varstatus"])
        time.sleep(0.1)
        print("Checking agaisnt repsonse" + response)
        print("Type is " + str(type(response)))
        print("OK! status homed" in str(response))
        if "OK! status homed" in response:
            return True
        else:
            return False

    def home(self, skip_if_homed=True) -> None:
        if not skip_if_homed:
            self.send_command("home")
        else:
            if not self.is_homed():
                self.send_command("home")
            else:
                print("Skipping homing")

    def get_dimensions(self) -> None:
        self.send_command("dimstatus")

    def abort(self) -> None:
        self.send_command("abort")

    def retract(self) -> None:
        self.send_command("retract")

    def load(self, stack_id) -> None:
        stack_id -= 1
        self.send_command(f"l {stack_id}")
        print(f"Loaded plate into stack {stack_id}")

    def unload(self, stack_id) -> None:
        stack_id -= 1
        self.send_command(f"u {stack_id}")
        print(f"Unloaded plate from stack {stack_id}")

    def go_to(self, stack_id) -> None:
        stack_id -= 1
        self.send_command(f"sp {stack_id}", 30000)

    def set_plate_dimensions(self, plate_height, stack_height, plate_thickness) -> None:
        self.send_command(f"spd {plate_height} {stack_height} {plate_thickness}", 10000)

    def set_to_manual(self) -> None:
        self.send_command("m")

    def disconnect(self) -> None:
        if self.tcp:
            self.tcp.disconnect()

    def send_command(self, message, timeout=60000) -> str:
        if not self.tcp:
            raise ConnectionError("Not connected to any server.")
       # cmd = COMMANDS[message]
        self.tcp.clear_buffer()
        result = self.tcp.send_command(message)
        print(f"First response is: {result}")
        
        if "ACK!" not in result:
            raise ValueError(f"Invalid response: {result}")
        
        wait_response = self.wait_for_command(timeout)
        print(f"Second response is: {wait_response}")
        return wait_response

    def wait_for_command(self, timeout) -> None:
        response = ""
        if self.blocking and self.tcp:
            response = self.tcp.read_response(timeout=timeout)
            if response.lower().startswith(("error", "aborted")):
                self.abort()
                raise ValueError(f"Failed to complete command. Error: {response}")
        return response
    
if __name__ == "__main__":
    microserve = MicroServeDriver(ip="192.168.1.60")
    microserve.connect("192.168.1.60",1000)
    print("Homing microserve")
    microserve.get_dimensions()
    #microserve.is_homed()
    # microserve.home()
    # print("Microserve homed")
    # print("Going to 3")
    # microserve.go_to(8)
    # # microserve.unload(3)
    # print("Microserve went to 8")
    # microserve.unload(8)
    # print("Microserve unload plate")
    # microserve.load(8)
    # print("Microserve loaded plate ")
    # microserve.set_to_manual()
    # print("Microserve is in manual mode")
    # print("Microserve went to 5")
    # microserve.go_to(1)
    # print("Microserve went to 1")
    # microserve.go_to(7)
    # print("Microserve went to 7")
