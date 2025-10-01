import logging
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.plr_pb2  import Command, Config
from tools.grpc_interfaces.tool_base_pb2 import ExecuteCommandReply
import argparse 
from google.protobuf.struct_pb2 import Struct
from tools.grpc_interfaces.tool_base_pb2 import  SUCCESS, ERROR_FROM_TOOL
from tools.toolbox.python_subprocess import run_python_script

class PLRToolServer(ToolServer):
    toolType = "plr"
    config:Config

    def __init__(self) -> None:
        super().__init__()


    def _configure(self, request:Config) -> None:
        logging.info("Configuring PLR...")
        self.config = request
        return
        
        
    def RunScript(self, params:Command.RunScript) -> ExecuteCommandReply:
        s  = Struct()
        response = ExecuteCommandReply()
        response.return_reply = True
        response.response = SUCCESS
        try:
            result = run_python_script(params.script_content, blocking=True)
            logging.info(f"Script result is {result}")
            if response:
                s.update({'response':result})
            else:
                s.update({'response':''})
            response.meta_data.CopyFrom(s)
        except Exception as exc:
            logging.exception(exc)
            response.response = ERROR_FROM_TOOL
            response.error_message = str(exc)
        return response

    def RunLocalScript(self, params:Command.RunLocalScript) -> ExecuteCommandReply:
        s  = Struct()
        response = ExecuteCommandReply()
        response.return_reply = True
        response.response = SUCCESS
        try:
            if not params.path:
                raise ValueError("Path to script must be provided...")
            python_exe = None
            logging.info(f"Config is {self.config}")
            if self.config and self.config.python_exe:
                python_exe = self.config.python_exe
                logging.info(f"Using python executable from config: {python_exe}")
            result = run_python_script(f"exec(open(r'''{params.path}''').read())", blocking=True, python_exe=python_exe)
            logging.info(f"Script result is {result}")
            if response:
                s.update({'response':result})
            else:
                s.update({'response':''})
            response.meta_data.CopyFrom(s)
        except Exception as exc:
            logging.exception(exc)
            response.response = ERROR_FROM_TOOL
            response.error_message = str(exc)
        return response
     
             
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    serve(PLRToolServer(), str(args.port))
