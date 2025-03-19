import os
import queue
import time
import comtypes.client as cc
from tools.base_server import ABCToolDriver
import logging 
import subprocess 
import sys 

VWORKS_PROCESS = "VWorks.exe"

def kill_vworks() -> None:
    """force kill vworks"""
    try:
        subprocess.run(["taskkill", "/F", "/IM", VWORKS_PROCESS], 
                        check=False, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
        time.sleep(0.1)
    except Exception as e:
        logging.warning(f"Failed to kill VWorks on clean up")
        
if os.name == "nt":
    import pythoncom
    #from comtypes import GUID
    from comtypes.client import GetEvents

    class VWorksEventSink:
        def __init__(self, event_queue):
            self.event_queue = event_queue

        def InitializationComplete(self, *args):
            logging.info(f"Initialization complete: {args}")
            self.event_queue.put(("InitializationComplete", args))
            return 0
            
        def InitializationCompleteWithCode(self, *args):
            logging.info(f"Initialization complete with code: {args}")
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
            logging.info(f"Protocol completed: {protocol}")
            self.event_queue.put(("ProtocolComplete", protocol))

        def ProtocolAborted(self, *args):
            protocol = args[1] if len(args) > 1 else "unknown"
            logging.error(f"Protocol aborted: {protocol}")
            self.event_queue.put(("ProtocolAborted", protocol))

        def UnrecoverableError(self, *args):
            description = args[1] if len(args) > 1 else "unknown error"
            logging.error(f"Unrecoverable error: {description}")
            self.event_queue.put(("UnrecoverableError", description))

        def RecoverableError(self, *args):
            description = args[3] if len(args) > 3 else "unknown error"
            logging.error(f"Recoverable error: {description}")
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
    def __init__(self, init_com=False) -> None:
        self.live = False
        self.event_queue = queue.Queue()
        self.event_connection = None
        self.driver = None
    
        if os.name == "nt":
            kill_vworks()
            if init_com:
                pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
                logging.info("COM initialized in the driver")
            try:
                self.driver = cc.CreateObject("VWorks4.VWorks4API")
                self.event_sink = VWorksEventSink(self.event_queue)
                self.event_connection = GetEvents(self.driver, self.event_sink)
            except Exception as e:
                logging.error(f"Failed to create VWorks COM object: {e}")
                # Check if this is a COM initialization error
                if "CoInitialize has not been called" in str(e):
                    logging.error("COM not initialized. Make sure pythoncom.CoInitialize is called first")
                raise

    def __del__(self):
        try:
            if hasattr(self, 'driver') and self.driver:
                logging.info("Cleaning up BravoServer resources")
                self.driver.close()
                self.driver = None
                
            # Uninitialize COM in the same thread that initialized it
            if os.name == "nt":
                import pythoncom
                logging.debug("Uninitializing COM in server thread")
                pythoncom.CoUninitialize()
        except Exception as e:
            logging.error(f"Error during BravoServer cleanup: {e}")

    def login(self, user:str="administrator", psw:str="administrator") -> None:
        self.driver.Login(user, psw)
        time.sleep(2)
    
    def logout(self)-> None:
        if self.driver:
            try:
                self.driver.Logout()
            except Exception as e:
                logging.warning(f"Error during logout: {e}")

    def close(self) -> None:
        self.logout()

    def show_vworks(self, show:bool=True) -> None:
        logging.info(f"Showing VWorks window= {show}")
        self.driver.ShowVWorks(show)

    def run_protocol(self, protocol:str) -> None:
        
        if os.path.splitext(protocol)[1] != ".pro":
            raise RuntimeError("Invalid file type. Must be .pro")
        
        if not os.path.exists(protocol):
            raise FileNotFoundError(f"{protocol} does not exist.")
        
        try:
            self.show_vworks()
            logging.info(f"Loading protocol: {protocol}")
            self.driver.LoadProtocol(protocol)
            
            logging.info(f"Running protocol: {protocol}")
            self.driver.RunProtocol(protocol, 1)
            
            logging.info(f"Waiting for protocol completion: {protocol}")
            success = self.wait_for_protocol_completion(protocol)
            
            self.show_vworks(False)
            if not success:
                raise RuntimeError(f"Protocol did not complete successfully: {protocol}")
                
        except Exception as e:
            raise RuntimeError(f"Error running protocol {protocol}: {e}")
    
    def run_runset(self, runset_file:str) -> None:
        if os.path.splitext(runset_file)[1] != ".rst":
            raise RuntimeError("Invalid file type. Must be .rst")
        if not os.path.exists(runset_file):
            raise FileNotFoundError(f"{runset_file} does not exist.")
        try:
            self.show_vworks()
            self.driver.LoadRunsetFile(runset_file)
            success = self.wait_for_protocol_completion(runset_file)
            self.show_vworks(False)
            if not success:
                raise RuntimeError(f"Runset did not complete successfully: {runset_file}")
        except Exception as e:
            raise RuntimeError(f"Error running runset {runset_file}:{e}")
    
    def wait_for_protocol_completion(self, protocol_name, timeout=300):
        start_time = time.time()
        last_event_type = None
        last_event_data = None
        
        # Message pump for COM events - keep processing Windows messages
        while True:
            pythoncom.PumpWaitingMessages()
            # Check if we've received completion events
            try:
                # Non-blocking queue check
                event_type, event_data = self.event_queue.get_nowait()
                print(f"Event received: {event_type} - Data: {event_data}")
                
                last_event_type = event_type
                last_event_data = event_data
                
                # For matching protocol names
                if event_type == "ProtocolComplete":
                    print(f"Protocol completion event received: {event_data}")
                    return True
                elif event_type == "ProtocolAborted":
                    print(f"Protocol aborted: {event_data}")
                    raise RuntimeError(f"Protocol was aborted: {protocol_name}")
                elif event_type == "UnrecoverableError":
                    print(f"Unrecoverable error occurred: {event_data}")
                    raise RuntimeError(f"Unrecoverable error: {event_data}")
                elif event_type == "RecoverableError":
                    print(f"Recoverable error occurred: {event_data}")
                    # Continue execution for recoverable errors, but log it
            except queue.Empty:
                # No events in the queue, continue waiting
                pass
            
            # Check timeout
            if time.time() - start_time > timeout:
                # If we timed out, report the last event we received
                error_msg = f"Timed out waiting for protocol completion: {protocol_name}"
                if last_event_type:
                    error_msg += f". Last event was {last_event_type}: {last_event_data}"
                else:
                    error_msg += ". No events were received"
                raise TimeoutError(error_msg)
            
            # Short sleep to avoid hammering the CPU
            time.sleep(0.28)

    def close(self):
        """Properly clean up resources"""
        if self.driver:
            self.driver.Logout()
            self.event_connection = None
        if os.name == "nt":
            try:
                # Try to logout first if logged in
                if hasattr(self, 'driver') and self.driver:
                    try:
                        self.driver.Logout()
                    except:
                        pass
                kill_vworks()
                # Give VWorks time to process the logout
                time.sleep(2)
                    
                if hasattr(self, 'event_connection') and self.event_connection:
                    print("Disconnecting event sink")
                    self.event_connection = None
                    
                # Don't explicitly set driver to None - let Python's GC handle it
            except Exception as e:
                print(f"Error during cleanup: {e}")

# if __name__ == "__main__":
#    # kill_vworks()
#     vworks = None
#     # try:
#     vworks = BravoDriver()
#     vworks.login()
#     vworks.run_runset("C:\\VWorks Workspace\\RunSet Files\\move_to_location_3.rst")
#         # Wait for any final messages to process
#     # except Exception as e:
#     #     print(f"Error running protocol: {e}")
#     # finally:
#     #     if vworks:
#     #         print("Cleaning up resources")
#     #         vworks.close()
#     #     sys.exit(0)