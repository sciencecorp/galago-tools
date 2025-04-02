
import logging.handlers
import logging
import os
import sys
import subprocess
from tools.app_config import Config
import socket 
import signal as os_signal
import time
import argparse
from os.path import dirname
from tools.utils import get_shell_command 

ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))
LOG_TIME = int(time.time())
TOOLS_32BITS = ["vcode","bravo","hig_centrifuge","plateloc","vspin"]

sys.path = [
    p for p in sys.path
    if not any(sub in p.lower() for sub in ["anaconda3", "miniconda", "mamba"])
]

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', 
)

class LaunchConsole():
    def __init__(self, config:Config) -> None:
        self.running_tools = 0
        self.config_file = ""
        logging.info("Starting Galago Manager")
        self.config :Config = config
        working_dir = "" 
        self.log_folder = os.path.join(working_dir,"data","trace_logs", str(LOG_TIME))
        self.server_processes : dict[str,subprocess.Popen] = {}
        
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)

    def kill_all_processes(self) ->None:
        logging.info("Killing all processes")
        for proc_key, process in self.server_processes.items():
            try:
                self.kill_by_process_id(process.pid)
                time.sleep(0.5)
                logging.info(f"Killed process {process.pid}")
                del process
            except ProcessLookupError as e:
                logging.error(f"failed to shut down process. Error={str(e)}")
                pass
        self.server_processes.clear()
        self.force_kill_tool()
    
    def load_tools(self) -> None:
        self.config.load_workcell_config()
 
    def read_last_lines(self, filename:str, lines:int=100) -> list[str]:
        with open(filename, 'rb') as f:
            f.seek(0, os.SEEK_END)
            end_position = f.tell()
            buffer_size = 1024
            blocks = -1
            data = []
            while end_position > 0 and len(data) < lines:
                if end_position - buffer_size > 0:
                    f.seek(blocks * buffer_size, os.SEEK_END)
                else:
                    f.seek(0, os.SEEK_SET)
                data.extend(f.readlines())
                end_position -= buffer_size
                blocks -= 1
            return [line.decode('utf-8') for line in data[-lines:]]
    
    def __del__(self) -> None:
        self.kill_all_processes()
    
    def kill_by_process_id(self, process_id:int) -> None:
        try:
            if os.name == 'nt':
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(process_id)])
            else:
                os.kill(process_id, os_signal.SIGINT)
        except ChildProcessError as e:
            logging.info(f"Failed to kill process {process_id}. Reason is={str(e)}")
        finally:
            return None

    def run_subprocess(self, tool_type:str, tool_name:str, port:int,confirm_modal:bool=False) -> None:
        try:
            self.kill_process_by_name(str(tool_name))
            tool_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = tool_socket.connect_ex(('127.0.0.1',int(port)))
            if result != 0:
                cmd = get_shell_command(tool_type=tool_type, port=port)
                os.chdir(ROOT_DIR)
                use_shell = False
                if os.name == 'nt':
                    use_shell = True
                logging.info(f"log folder is {self.log_folder}")
                # if self.log_folder:
                #     output_file = join(self.log_folder, str(tool_name)) + ".log"
                #     process = subprocess.Popen(cmd, stdout=open(output_file,'w'), stderr=subprocess.STDOUT,  universal_newlines=True)
                # else:
                process = subprocess.Popen(cmd, shell=use_shell,universal_newlines=True)
                self.server_processes[tool_name] = process
            else:
                logging.warning(f"Port {port} for {tool_name} is already occupied")
        except subprocess.CalledProcessError:
            logging.info("There was an error launching tool server.")
        return None
    
    def kill_process_by_name(self, process_name:str) -> None:
        if process_name not in self.server_processes.keys():
            return None
        else:
            try:
                process_id = self.server_processes[process_name].pid
                self.kill_by_process_id(process_id)
            except Exception as e:
                logging.warning(f"Failed to kill process {process_name}. Reason is={str(e)}.")
        return None 
    
    def force_kill_tool(self) -> None:
        try:
            if os.name != 'nt':
                subprocess.Popen("lsof -t -i tcp:1010 | xargs kill", shell=True)
        except Exception as e:
            logging.error(f"Failed to force kill toolbox. Reason is {str(e)}")

    def start_toolbox(self) -> None:
        logging.info("Launching Toolbox")
        try:
            self.run_subprocess("toolbox", "Tool Box",1010,False)
        except subprocess.CalledProcessError:
            logging.info("There was an error launching toolbox server.")

    def run_all_tools(self) -> None:
        self.kill_all_processes()
        time.sleep(0.5)
        self.load_tools()
        self.start_toolbox()
        if self.config.workcell_config is None:
            logging.error("No workcell configuration loaded")
            return

        for t in self.config.workcell_config.tools:
            logging.info(f"Launching process for tool {t.name}")
            #Check if tool is already running. 
            tool_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = tool_socket.connect_ex(('127.0.0.1',t.port))
            if result != 0:
                try:
                    self.run_subprocess(t.type,t.name,t.port,False )
                except Exception as e:
                    logging.error(f"Failed to launch tool {t.name}. Error is {e}")
            else:
                logging.warning(f"Port for tool {t.name} is already occupied")
        time.sleep(0.5)

def main() -> int:
    parser = argparse.ArgumentParser(description='Launch Galago Tools Manager')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with detailed logging')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s | %(levelname)s | %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    try:
        config = Config()
        #config.load_app_config()
        logging.info("Loading workcell config")
        config.load_workcell_config()
        manager = LaunchConsole(config)
        manager.run_all_tools()

        logging.info("Tool servers are running. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
        return 0
    except KeyboardInterrupt:
        logging.info("Shutdown requested by user.")
        manager.kill_all_processes()
        return 0
    except Exception:
        logging.exception("Failed to launch tools")
        sys.exit(1)
        return 1
    
if __name__ == "__main__":
    main()