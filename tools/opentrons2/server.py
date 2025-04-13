import typing as t
import logging
import os
import re
import tempfile
import time

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.opentrons2_pb2 import Command, Config
from google.protobuf import json_format
from tools.app_config import Config as AppConfig 
from .driver import Ot2Driver
import argparse

class Opentrons2Server(ToolServer):
    toolType = "opentrons2"
    driver: Ot2Driver
    config: Config
    
    def __init__(self) -> None:
          super().__init__()
          self.app_config = AppConfig()
          self.driver_config : Config 
          self.process_images : bool = True 
          
    def _configure(self, config: Config) -> None:
        self.driver_config = config
        self.driver = Ot2Driver(robot_ip=config.robot_ip, robot_port=config.robot_port)
        self.driver.ping()

    def _createProgramFromTemplate(self, templatePath: str, params: dict[t.Any, t.Any]) -> str:
        """
        Creates a program from a template and parameters, creates a new temporary file and returns the path to it
        """
        template = open(templatePath).read()
        params_str = str(params)
        # HACK: strip out the trailing .0 on any numbers, because protobuf turns all ints into floats
        params_str = re.sub(r"(\d)\.0\b", r"\1", params_str)
        program = re.sub(
            r"#.*PARAMS_START.*\n[\s\S]*\n#.*PARAMS_END.*\n",
            "params = %s\n" % params_str,
            template,
            re.MULTILINE,
        )
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write(program)
            logging.info(f"Created temporary program {f.name}")
            return f.name

    def RunProgram(self, params: Command.RunProgram) -> None:
        #today : str = datetime.today().strftime('%Y-%m-%d')
        #pre_run_name = f"ot2_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_pre_run.jpg"
        #self.driver.take_picture(pre_run_name, os.path.join(self.app_config.app_config.data_folder,"images","ot2",today))
        if params.program_name == "universal_opentrons_json_executor":
            program_dir = os.path.dirname(os.path.abspath(__file__))
        else:
            program_dir = self.config.program_dir
        program_path = os.path.join(program_dir, params.program_name + ".py")
        program_params = params.params
        logging.info(f"Running program {program_path} with params {program_params}")
        params_dict = json_format.MessageToDict(program_params)
        program = self._createProgramFromTemplate(templatePath=program_path, params=params_dict)
        self.driver.start_protocol(protocol_file=program)
       # post_run_name = f"ot2_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_pre_run.jpg"
        #self.driver.take_picture(post_run_name, os.path.join(self.app_config.app_config.data_folder,"images","ot2",today))
    
    def Sleep(self, params: Command.Sleep) -> None:
        logging.info(f"Sleeping for {params.seconds} seconds")
        time.sleep(params.seconds)

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

    def EstimateSleep(self, params: Command.Sleep) -> int:
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
    serve(Opentrons2Server(), os.environ.get("PORT", str(args.port)))
