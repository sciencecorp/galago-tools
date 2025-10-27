import logging
import os

from google.protobuf.struct_pb2 import Struct
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.tool_base_pb2 import ExecuteCommandReply
from tools.grpc_interfaces.opentrons2_pb2 import Command, Config
from google.protobuf import json_format
from tools.app_config import Config as AppConfig 
from .driver import Ot2Driver
import argparse
from .utils import run_opentrons_simulation, create_executable_script, check_opentrons_installation
from tools.grpc_interfaces.tool_base_pb2 import  SUCCESS, ERROR_FROM_TOOL

class Opentrons2Server(ToolServer):
    toolType = "opentrons2"
    driver: Ot2Driver
    config: Config
    
    def __init__(self) -> None:
        super().__init__()
        self.app_config = AppConfig()
        self.driver_config: Config 
        self.process_images: bool = True 
          
    def _configure(self, config: Config) -> None:
        self.driver_config = config
        self.driver = Ot2Driver(robot_ip=config.robot_ip, robot_port=config.robot_port)
        # self.driver.ping()


    def RunProgram(self, params: Command.RunProgram) -> ExecuteCommandReply:
        """
        Execute a Python script with variables passed directly in the request.
        """
        s = Struct()
        response = ExecuteCommandReply()
        response.return_reply = True
        response.response = SUCCESS
        script_content = params.script_content
        variables_dict = json_format.MessageToDict(params.variables) if params.variables else {}
        logging.info(f"Running program with {len(variables_dict)} variables")
        
        try:
            # Process the script and create executable file with injected variables
            executable_script = create_executable_script(script_content, variables_dict)
            logging.info(f"Created executable script at: {executable_script}")

            if params.simulate:
                logging.info("Simulating protocol...")
                success, stdout, stderr = run_opentrons_simulation(executable_script, verbose=True)
                if not success:
                    raise RuntimeError(f"Simulation failed:\n{stderr}")
                logging.info("Simulation completed successfully.")
                result = stdout 
            else:
                # Execute the script on the OT-2
                logging.info("Starting protocol on OT-2...")
                result = self.driver.start_protocol(protocol_file=executable_script)
                
            # Populate response with result
            logging.info(f"Program result: {result}")
            if result:
                s.update({'response': result})
            else:
                s.update({'response': ''})
            response.meta_data.CopyFrom(s)
            
            # Cleanup temporary file
            try:
                os.unlink(executable_script)
                logging.info(f"Cleaned up temporary script: {executable_script}")
            except OSError as e:
                logging.warning(f"Could not delete temporary file {executable_script}: {e}")
                
        except Exception as exc:
            logging.exception(exc)
            response.response = ERROR_FROM_TOOL
            response.error_message = str(exc)
            
        return response

    def Pause(self, params: Command.Pause) -> None:
        logging.info("Pausing program")
        self.driver.pause_protocol()

    def Resume(self, params: Command.Resume) -> None:
        logging.info("Resuming program")
        self.driver.resume_protocol()

    def Cancel(self, params: Command.Cancel) -> None:
        logging.info("Canceling program")
        self.driver.cancel_protocol()

    def ToggleLight(self, params: Command.ToggleLight) -> None:
        logging.info("Toggling light")
        self.driver.toggle_light()

    def EstimateRunProgram(self, params: Command.RunProgram) -> int:
        return 1

    def EstimatePause(self, params: Command.Pause) -> int:
        return 1

    def EstimateResume(self, params: Command.Resume) -> int:
        return 1

    def EstimateCancel(self, params: Command.Cancel) -> int:
        return 1

    def EstimateToggleLight(self, params: Command.ToggleLight) -> int:
        return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    serve(Opentrons2Server(), str(args.port))