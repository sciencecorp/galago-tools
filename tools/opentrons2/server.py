import logging
import os
import tempfile

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.opentrons2_pb2 import Command, Config
from google.protobuf import json_format
from tools.app_config import Config as AppConfig 
from .driver import Ot2Driver
import argparse
import json 

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
        # self.driver = Ot2Driver(robot_ip=config.robot_ip, robot_port=config.robot_port)
        # self.driver.ping()

    def _create_executable_script(self, script_content: str, variables: dict) -> str:
        """
        Create an executable script by injecting variables at the top of the script.
        """
        # Create the variables definition section
        variables_section = "# Injected variables\n"
        
        for key, var_data in variables.items():
            # Extract the actual variable name and value from the variable data structure
            if isinstance(var_data, dict) and 'name' in var_data and 'value' in var_data:
                var_name = var_data['name']
                raw_value = var_data['value']
                var_type = var_data.get('type', 'string')
                
                # Parse the value based on its type
                if var_type == 'array':
                    # Parse JSON array string
                    try:
                        parsed_value = json.loads(raw_value)
                        variables_section += f'{var_name} = {repr(parsed_value)}\n'
                    except json.JSONDecodeError:
                        logging.warning(f"Failed to parse array variable {var_name}: {raw_value}")
                        variables_section += f'{var_name} = []\n'
                        
                elif var_type == 'boolean':
                    # Parse boolean string
                    bool_value = raw_value.lower() in ('true', '1', 'yes', 'on')
                    variables_section += f'{var_name} = {bool_value}\n'
                    
                elif var_type == 'number':
                    # Parse number string
                    try:
                        if '.' in str(raw_value):
                            parsed_value = float(raw_value)
                        else:
                            parsed_value = int(raw_value)
                        variables_section += f'{var_name} = {parsed_value}\n'
                    except (ValueError, TypeError):
                        logging.warning(f"Failed to parse number variable {var_name}: {raw_value}")
                        variables_section += f'{var_name} = 0\n'
                        
                elif var_type == 'string':
                    variables_section += f'{var_name} = "{raw_value}"\n'
                    
                else:
                    # Fallback for unknown types
                    variables_section += f'{var_name} = "{raw_value}"\n'
                    
            else:
                # Handle case where key is the variable name and var_data is the direct value
                var_name = str(key)
                if isinstance(var_data, str):
                    variables_section += f'{var_name} = "{var_data}"\n'
                elif isinstance(var_data, (list, dict)):
                    variables_section += f'{var_name} = {repr(var_data)}\n'
                else:
                    variables_section += f'{var_name} = {var_data}\n'
        
        variables_section += "\n# End injected variables\n\n"
        
        # Combine variables with the script content
        processed_script = variables_section + script_content
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write(processed_script)
            logging.info(f"Created executable script: {f.name}")
            return f.name

    def RunProgram(self, params: Command.RunProgram) -> None:
        """
        Execute a Python script with variables passed directly in the request.
        """
        script_content = params.script_content
        variables_dict = json_format.MessageToDict(params.variables) if params.variables else {}
        logging.info(f"Running program with {len(variables_dict)} variables")
        try:
            # Process the script and create executable file with injected variables
            executable_script = self._create_executable_script(script_content, variables_dict)
            
            # Execute the script on the OT-2
            self.driver.start_protocol(protocol_file=executable_script)
            
            # Cleanup temporary file
            try:
                os.unlink(executable_script)
                logging.info(f"Cleaned up temporary script: {executable_script}")
            except OSError as e:
                logging.warning(f"Could not delete temporary file {executable_script}: {e}")
                
        except Exception as e:
            logging.error(f"Error running program: {e}")
            raise

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