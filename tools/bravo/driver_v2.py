import os
import threading
import queue
import time
import comtypes.client as cc
from tools.base_server import ABCToolDriver


def find_vworks_progid():
    possible_ids = [
        "VWorks4.VWorks4API",
        "VWorks.Application",
        "Agilent.VWorks.Application",
        "VWorks4COM.VWorks4Controller"
    ]
    
    for progid in possible_ids:
        print(f"Prog id {progid}")
        try:
            obj = cc.CreateObject(progid)
            print(f"Found progid")
            print(obj)
            print(progid)
            return progid
        except:
            continue
    
    raise RuntimeError("Could not find VWorks COM object")

if os.name == "nt":
    import clr
    import pythoncom
    from comtypes import GUID
    from comtypes.client import GetEvents

    class VWorksEventSink:
        def __init__(self, event_queue):
            self.event_queue = event_queue

        def InitializationComplete(self, *args):
            print(f"Initialization complete: {args}")
            self.event_queue.put(("InitializationComplete", args))
            return 0
            
        def InitializationCompleteWithCode(self, *args):
            print(f"Initialization complete with code: {args}")
            self.event_queue.put(("InitializationCompleteWithCode", args))
            return 0

        def LogMessage(self, *args):
            # This fires frequently with many arguments, so just accept all of them
            # Don't put in queue to reduce overhead
            return 0
            
        # def MessageBoxAction(self, *args):
        #     message = args[2] if len(args) > 2 else "Unknown message"
        #     print(f"Message box action: {message}")
        #     self.event_queue.put(("MessageBoxAction", message))
            
        #     # Return explicit button choice (1 = OK, 2 = Cancel)
        #     # For compiler errors, choose Cancel (2) which is recommended
        #     if "compiler errors" in message:
        #         return 2  # Cancel
        #     else:
        #         return 1  # OK
            
        # def UserMessage(self, *args):
        #     message = args[1] if len(args) > 1 else "Unknown message"
        #     print(f"User message: {message}")
        #     self.event_queue.put(("UserMessage", message))
        #     return 0
            
        def ProtocolComplete(self, *args):
            protocol = args[1] if len(args) > 1 else "unknown"
            print(f"Protocol completed: {protocol}")
            self.event_queue.put(("ProtocolComplete", protocol))
            return 0

        def ProtocolAborted(self, *args):
            protocol = args[1] if len(args) > 1 else "unknown"
            print(f"Protocol aborted: {protocol}")
            self.event_queue.put(("ProtocolAborted", protocol))
            return 0

        def UnrecoverableError(self, *args):
            description = args[1] if len(args) > 1 else "unknown error"
            print(f"Unrecoverable error: {description}")
            self.event_queue.put(("UnrecoverableError", description))
            return 0

        def RecoverableError(self, *args):
            description = args[3] if len(args) > 3 else "unknown error"
            print(f"Recoverable error: {description}")
            self.event_queue.put(("RecoverableError", description))
            
            # If we have action parameters
            if len(args) > 4:
                actionToTake = args[4]
                if hasattr(actionToTake, "value"):
                    actionToTake.value = 0  # 0=Abort, 1=Retry, 2=Ignore
            
            if len(args) > 5:
                vworksHandlesError = args[5]
                if hasattr(vworksHandlesError, "value"):
                    vworksHandlesError.value = True  # Let VWorks handle the error
                    
        
    # GUID for the event interface - you might need to adjust this
    # This should match the GUID for _IVWorks4APIEvent in the registry
    # IVWorks4APIEvent = GUID("{EB350F99-1AC0-429E-8213-55D57DC010C1}")  # Example GUID, replace with correct one

else:
    # Dummy definitions for non-Windows OS
    class VWorksEventSink:
        pass

    class VWorks4API:
        # Your dummy class implementation...
        pass

class BravoDriver(ABCToolDriver):
    def __init__(self) -> None:
        self.live = False
        self.event_queue = queue.Queue()
        self.event_connection = None
        self.driver = None
        
    
        if os.name == "nt":
            pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
            # Create the COM object
            self.driver = cc.CreateObject("VWorks4.VWorks4API")
            
            # Create and connect event sink
            self.event_sink = VWorksEventSink(self.event_queue)
            self.event_connection = GetEvents(self.driver, self.event_sink)
            print("VWorks COM object created and events connected")

            #self.driver = VWorks4API()
    
    def __del__(self):
        """Destructor for cleanup"""
        self.close()
        if os.name == "nt":
            print("Uninitializing COM")
            pythoncom.CoUninitialize()
        
    def login(self, user:str="administrator", psw:str="administrator") -> None:
        self.driver.Login(user, psw)
        time.sleep(1)
    
    def run_protocol(self, protocol:str) -> None:
        if not os.path.exists(protocol):
            raise FileNotFoundError(f"{protocol} does not exist.")
        self.login()
        self.driver.LoadProtocol(protocol)
        self.driver.RunProtocol(protocol, 1)
        self.wait_for_protocol_completion(protocol)
    
    def run_runset(self, runset_file:str) -> None:
        if not os.path.exists(runset_file):
            raise FileNotFoundError(f"{runset_file} does not exist.")
        self.login()
        self.driver.LoadRunsetFile(runset_file)
        self.wait_for_protocol_completion(runset_file)
    
    def wait_for_protocol_completion(self, protocol_name, timeout=300):
        start_time = time.time()
        
        # Message pump for COM events - keep processing Windows messages
        while True:
            pythoncom.PumpWaitingMessages()
            
            # Check if we've received completion events
            try:
                event_type, event_data = self.event_queue.get_nowait()
                if event_type == "ProtocolComplete" and protocol_name in event_data:
                    print(f"Protocol completed: {protocol_name}")
                    return True
                elif event_type == "ProtocolAborted" and protocol_name in event_data:
                    print(f"Protocol aborted: {protocol_name}")
                    return False
                elif event_type == "UnrecoverableError":
                    print(f"Unrecoverable error occurred: {event_data}")
                    raise RuntimeError(f"Unrecoverable error: {event_data}")
                elif event_type == "RecoverableError":
                    print(f"Recoverable error occurred: {event_data}")
            except queue.Empty:
                pass
            
            # Check timeout
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Timed out waiting for protocol completion: {protocol_name}")
            
            
            time.sleep(0.1)

    def close(self):
        """Properly clean up resources"""
        if os.name == "nt":
            try:
                # Try to logout first if logged in
                if hasattr(self, 'driver') and self.driver:
                    try:
                        self.driver.Logout()
                    except:
                        pass
                    
                # Give VWorks time to process the logout
                time.sleep(2)
                    
                if hasattr(self, 'event_connection') and self.event_connection:
                    print("Disconnecting event sink")
                    self.event_connection = None
                    
                # Don't explicitly set driver to None - let Python's GC handle it
            except Exception as e:
                print(f"Error during cleanup: {e}")

if __name__ == "__main__":

    # print(find_vworks_progid())
    vworks = None
    try:
        vworks = BravoDriver()
        vworks.run_protocol("C:\\VWorks Workspace\\Protocol Files\\generic\\move_to_location_3.pro")
        # Wait for any final messages to process
        time.sleep(3)  
    except Exception as e:
        print(f"Error running protocol: {e}")
    finally:
        if vworks:
            print("Cleaning up resources")
            vworks.close()