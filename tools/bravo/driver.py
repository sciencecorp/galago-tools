import os
from tools.base_server import ABCToolDriver
import time 

if os.name == "nt":
    import clr  # type: ignore
    SDK_DLL = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "deps",
            "Interop.VWorks4Lib.dll",
        )
    clr.AddReference(SDK_DLL)  

    from VWorks4Lib import VWorks4API # type: ignore

else:
    #Dummy class for non Windows OS
    class VWorks4API: # type: ignore
        def __init__(self) -> None:
            pass

        def Initialize(self) -> None:
            raise NotImplementedError(
                "VWorks interface is not supported on non-Windows platforms"
            )
        
        def LoadDeviceFile(self) -> None:
            raise NotImplementedError(
                "VWorks interface is not supported on non-Windows platforms"
            )
        
        def RunProtocol(self, protocol_file:str) -> None:
            raise NotImplementedError(
                "VWorks interface is not supported on non-Windows platforms"
            ) 
          
        def RunRunset(self, runset_file:str) -> None:
            raise NotImplementedError(
                "VWorks interface is not supported on non-Windows platforms"
            )  
        

COMPLETE_FILE_FLAG = "C:\\VWorks Workspace\\FRT\\complete.txt"
ERROR_FILE_FLAG = "C:\\VWorks Workspace\\FRT\\complete.txt"

class BravoDriver(ABCToolDriver):
    def __init__(self) -> None:
        self.live : bool  = False
        self.driver = VWorks4API()
        # self._event_lock: threading.Lock = threading.Lock()
        # self.event_queue = queue.Queue = queue.Queue()
        # self.driver.ProtocolComplete += self.wait_for_protocol
    
    def login(self, user:str="administrator", psw:str="administrator") -> None:
        self.driver.Login(user,psw)
        time.sleep(5)

    def run_protocol(self, protocol:str) -> None:
        if not os.path.exists(protocol):
            raise FileNotFoundError(f"{protocol} does not exist.")
        self.login()
        self.driver.LoadProtocol(protocol)
        time.sleep(5)
        self.driver.RunProtocol(protocol, 1)
        # self.wait_for_protocol()

    def run_runset(self, runset_file:str) -> None:
        if not os.path.exists(runset_file):
            raise FileNotFoundError(f"{runset_file} does not exist.")
        if os.path.exists(COMPLETE_FILE_FLAG):
            os.remove(COMPLETE_FILE_FLAG)
        self.driver.LoadRunsetFile(runset_file)
        self.wait_for_protocol()

    #I was not able to subscribe to the VWorks events api, this not ideal approach is to wait for a completion 
    #flag, generated through the vworks protocol at the end of the run.
    def wait_for_protocol(self, timeout :int = 300) -> None:
        start_time = time.time()
        while True:
            seconds_spent_waiting = int(time.time() - start_time)
            if timeout and seconds_spent_waiting > timeout:
                raise Exception(
                    "Run protocol has timed out. Please reset VWorks and restart the driver."
                )
            if os.path.exists(COMPLETE_FILE_FLAG):
                #wait 2 seconds for vworks to close the runset after the file is created
                time.sleep(3)
                break
            time.sleep(1)

if __name__ == "__main__":
    vworks = BravoDriver()
    #vworks.run_runset("C:\\VWorks Workspace\\Runset Files\\test.rst")
    vworks.run_protocol("C:\\VWorks Workspace\\Protocol Files\\test.pro")