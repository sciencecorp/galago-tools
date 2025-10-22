import logging
import os
import argparse
import threading
import time
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.bravo_pb2 import Command, Config
from .driver import BravoDriver, kill_vworks
from typing import Callable, Any 

if os.name == "nt":
    import pythoncom
    
_thread_local = threading.local()

class BravoServer(ToolServer):
    toolType = "bravo"
    config: Config
    
    def __init__(self) -> None:
        super().__init__()
        self.main_thread_id = threading.get_ident()
        logging.info(f"BravoServer initialized in thread ID: {self.main_thread_id}")
        
        # Initialize COM in the main thread
        if os.name == "nt":
            pythoncom.CoInitialize()
            logging.info("COM initialized in main thread")
        
        # Flag to signal server shutdown
        self.shutdown = False
    
    def _configure(self, request: Config) -> None:
        logging.info(f"Configuring Bravo in thread ID: {threading.get_ident()}")
        self.config = request
        logging.info("Bravo configuration complete")
    
    def _get_thread_driver(self, force_new:bool=False) -> Any:

        thread_id = threading.get_ident()
        
        # Check if we need to initialize COM for this thread
        if not hasattr(_thread_local, 'com_initialized'):
            logging.info(f"Initializing COM in thread ID: {thread_id}")
            pythoncom.CoInitialize()
            _thread_local.com_initialized = True
        
        # Create or verify existing driver
        try:
            # If we need a new driver or don't have one
            if force_new or not hasattr(_thread_local, 'driver'):
                # If we had a previous driver, try to close it properly
                if hasattr(_thread_local, 'driver'):
                    try:
                        logging.info(f"Closing previous driver in thread ID: {thread_id}")
                        _thread_local.driver.close()
                    except Exception as e:
                        logging.warning(f"Error closing previous driver: {e}")
                
                # Force kill VWorks to ensure clean state
                kill_vworks()
                time.sleep(0.5)
                
                # Create new driver
                logging.info(f"Creating new BravoDriver in thread ID: {thread_id}")
                _thread_local.driver = BravoDriver(init_com=False)
                _thread_local.driver.login()
                logging.info(f"BravoDriver created and logged in for thread ID: {thread_id}")
            else:
                # Verify the existing driver is still responsive
                try:
                    # Try to pump messages which will fail if COM is disconnected
                    pythoncom.PumpWaitingMessages()
                except Exception as e:
                    logging.warning(f"COM connection test failed, recreating driver: {e}")
                    return self._get_thread_driver(force_new=True)
            
            return _thread_local.driver
            
        except Exception as e:
            logging.error(f"Failed to create BravoDriver in thread {thread_id}: {e}")
            # Clean up and try again with a fresh environment
            if hasattr(_thread_local, 'driver'):
                try:
                    _thread_local.driver.close()
                except Exception as e:
                    logging.warning(f"Failed to close BravoDriver: {e}")
                delattr(_thread_local, 'driver')
            
            # If this is already a retry, give up to avoid infinite recursion
            if force_new:
                raise RuntimeError(f"Failed to initialize Bravo driver after recovery attempt: {str(e)}")
            
            # Try once more with force_new=True
            logging.info("Attempting recovery by creating a fresh driver")
            kill_vworks()  # Make sure VWorks is killed
            time.sleep(1)  # Give more time for cleanup
            return self._get_thread_driver(force_new=True)
    
    def cleanup(self) -> None:
        """Clean up resources properly for all threads"""
        logging.info(f"Cleanup called from thread ID: {threading.get_ident()}")
        
        # Signal shutdown
        self.shutdown = True
        
        # Clean up the driver in the current thread if it exists
        if hasattr(_thread_local, 'driver'):
            try:
                logging.info(f"Cleaning up driver for thread ID: {threading.get_ident()}")
                _thread_local.driver.close()
                delattr(_thread_local, 'driver')
            except Exception as e:
                logging.error(f"Error closing driver: {e}")
        
        # Clean up COM in the current thread if it was initialized
        if hasattr(_thread_local, 'com_initialized'):
            try:
                logging.info(f"Uninitializing COM in thread ID: {threading.get_ident()}")
                pythoncom.CoUninitialize()
                delattr(_thread_local, 'com_initialized')
            except Exception as e:
                logging.error(f"Error uninitializing COM: {e}")
        
        # Make sure VWorks is killed
        kill_vworks()
    
    def _execute_with_retry(
        self,
        operation_name: str,
        operation_func: Callable[[BravoDriver], None],
        max_retries: int = 2
    ) -> None:
        """Execute an operation with automatic retry on RPC errors"""
        retries = 0
        last_error = None
        while retries <= max_retries:
            try:
                if retries > 0:
                    logging.info(f"Retry #{retries} for {operation_name}")
                    # If we're retrying, force a new driver
                    driver = self._get_thread_driver(force_new=True)
                else:
                    # First attempt uses existing or new driver
                    driver = self._get_thread_driver()
                
                # Process COM messages before running
                if os.name == "nt":
                    pythoncom.PumpWaitingMessages()
                
                # Run the operation
                return operation_func(driver)
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # Check if this is an RPC error
                if "RPC server is unavailable" in error_str or "marshalled for a different thread" in error_str:
                    logging.warning(f"RPC connection error in {operation_name}: {e}")
                    retries += 1
                    # Force kill VWorks
                    logging.info("RPC unavailable killing vworks")
                    kill_vworks()
                    time.sleep(1)  # Wait before retry
                else:
                    # This is not an RPC error, don't retry
                    logging.error(f"Non-RPC error in {operation_name}: {e}")
                    raise
        
        # If we exhausted all retries
        logging.error(f"Failed {operation_name} after {max_retries} retries")
        raise last_error
    
    def RunProtocol(self, params: Command.RunProtocol) -> None:
        thread_id = threading.get_ident()
        logging.info(f"RunProtocol called from thread ID: {thread_id}")
        
        def run_op(driver:BravoDriver) -> None:
            return driver.run_protocol(params.protocol_file)
        
        self._execute_with_retry("RunProtocol", run_op)
    
    def RunRunset(self, params: Command.RunRunset) -> None:
        thread_id = threading.get_ident()
        logging.info(f"RunRunset called from thread ID: {thread_id}")
        def run_op(driver: BravoDriver) -> None:
            return driver.run_runset(params.runset_file)
        
        self._execute_with_retry("RunRunset", run_op)
   
    def EstimateRunProtocol(self, params: Command.RunProtocol) -> int:
        return 60  # Return a more realistic estimate in seconds
    
    def EstimateRunRunset(self, params: Command.RunRunset) -> int:
        return 120  # Return a more realistic estimate in seconds
    
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s', 
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True, help='Port for the gRPC server')
    args = parser.parse_args()
    
    server = None
    args = parser.parse_args()
    if not args.port:
        raise RuntimeWarning("Port must be provided...")
    serve(BravoServer(), str(args.port))