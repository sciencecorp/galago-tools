import logging
import os
import argparse 
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.bravo_pb2 import Command, Config
from .driver import VPrepDriver

class VPrepServer(ToolServer):
    toolType = "vprep"
    config: Config
    
    def __init__(self) -> None:
        super().__init__()
        self.driver = None  # Initialize to None, create it during _configure
    
    def _configure(self, request: Config) -> None:
        logging.info("Initializing VPrep")
        self.config = request
        
        try:
            # Ensure we're in the main thread when creating the driver
            # which will initialize COM
            if os.name == "nt":
                import pythoncom
                # Initialize COM in the server thread
                pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
                logging.debug("COM initialized in server thread")
            
                self.driver = VPrepDriver()  # Create the driver after COM is initialized
                logging.debug("Logging into VWorks")
                self.driver.login()
                logging.info("VWorks login successful")
            else:
                raise RuntimeError("VPrep server is only supported on Windows.")
        except Exception as e:
            error_msg = f"Failed to initialize VPrep driver: {str(e)}"
            logging.error(error_msg)
            raise RuntimeError(error_msg)
    
    def cleanup(self) -> None:
        """Clean up resources properly"""
        try:
            if hasattr(self, 'driver') and self.driver:
                logging.info("Cleaning up VPrep driver resources")
                self.driver.close()
                self.driver = None
                
            # Uninitialize COM in the same thread that initialized it
            if os.name == "nt":
                import pythoncom
                logging.debug("Uninitializing COM in server thread")
                pythoncom.CoUninitialize()
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
    
    def RunProtocol(self, params: Command.RunProtocol) -> None:
        if not self.driver:
            raise RuntimeError("Driver not initialized. Call configure first.")
        self.driver.run_protocol(params.protocol_file)
    
    def RunRunset(self, params: Command.RunRunset) -> None:
        if not self.driver:
            raise RuntimeError("Driver not initialized. Call configure first.")
        self.driver.run_runset(params.runset_file)
   
    def EstimateRunProtocol(self, params: Command.RunProtocol) -> int:
        return 1
    
    def EstimateRunRunset(self, params: Command.RunRunset) -> int:
        return 1
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    
    server = None
    try:
        if not args.port:
            raise RuntimeWarning("Port must be provided...")
        else:
            server = VPrepServer()
            serve(server, os.environ.get("PORT", str(args.port)))
    finally:
        if server:
            server.cleanup()