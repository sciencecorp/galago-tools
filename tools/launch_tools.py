import logging.handlers
import subprocess
from tools.app_config import Config
import threading
import socket 
import logging 
import os
import sys
import signal as os_signal
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import time
import argparse
from os.path import join, dirname
from typing import Optional, Any, Callable
from tkinter.scrolledtext import ScrolledText
from tools.utils import get_shell_command 
from pyfiglet import Figlet # type: ignore
import appdirs  # type: ignore

# Configuration flags
USE_APP_DATA_DIR = True  # Set to False for local development/testing

# Use appdirs to get platform-specific data directory
APP_NAME = "galago"
APP_AUTHOR = "galago"
DATA_DIR = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)

ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))
LOG_TIME = int(time.time())
TOOLS_32BITS = ["vcode","bravo","hig_centrifuge","plateloc","vspin"]

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', 
)

sys.path = [
    p for p in sys.path
    if not any(sub in p.lower() for sub in ["anaconda3", "miniconda", "mamba"])
]

class ToolsManager():

    def __init__(self, app_root:tk.Tk, config:Config) -> None:
        logging.info("Starting Galago Manager")
        self.root = app_root
        self.root.title("Tools Server Manager")
        self.set_icon()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.geometry('1000x700')  

        self.running_tools = 0
        self.config_file = ""
        self.config :Config = config
        
        # Set appropriate log directory based on configuration
        if USE_APP_DATA_DIR:
            # Use platform-specific app data directory (for production)
            self.log_folder = os.path.join(DATA_DIR, "trace_logs", str(LOG_TIME))
            logging.info(f"Using app data directory for logs: {self.log_folder}")
        else:
            # Use directory relative to ROOT_DIR (for local development/testing)
            self.log_folder = os.path.join(ROOT_DIR, "data", "trace_logs", str(LOG_TIME))
            logging.info(f"Using local directory for logs: {self.log_folder}")

        # Ensure the log directory exists
        try:
            if not os.path.exists(self.log_folder):
                os.makedirs(self.log_folder, exist_ok=True)
            logging.info(f"Created log directory: {self.log_folder}")
        except Exception as e:
            logging.error(f"Failed to create log directory: {self.log_folder}. Error: {str(e)}")
            # Fallback to a directory we know should work
            self.log_folder = os.path.join(os.path.expanduser("~"), "galago_logs", str(LOG_TIME))
            logging.warning(f"Using fallback log directory: {self.log_folder}")
            os.makedirs(self.log_folder, exist_ok=True)

        #Build databases if they do not exist
        self.server_processes : dict[str,subprocess.Popen] = {}
        self.tool_box_process: Optional[subprocess.Popen] = None
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        self.paned_window.propagate(False)

        left_width = 250  # Increased left frame width
        self.left_frame = tk.Frame(self.paned_window, width=left_width)
        self.left_frame.pack(fill=tk.BOTH, expand=True)
        self.left_frame.pack_propagate(False)

        self.left_scrollbar = ttk.Scrollbar(self.left_frame, orient=tk.VERTICAL)
        self.left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.left_canvas = tk.Canvas(self.left_frame, yscrollcommand=self.left_scrollbar.set)
        self.left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.left_scrollbar.config(command=self.left_canvas.yview)
        self.tool_buttons : dict[str, tuple[str,tk.Button,tk.Canvas]] = {}
        self.tool_buttons_previous_states : dict[str, bool] = {}

        # Create a frame inside the canvas to hold the widgets
        self.widgets_frame = ttk.Frame(self.left_canvas)
        self.widgets_frame.bind(
            "<Configure>",
            lambda e: self.left_canvas.configure(
                scrollregion=self.left_canvas.bbox("all")
            )
        )

        # Create a window inside the canvas
        self.left_canvas.create_window((0, 0), window=self.widgets_frame, anchor="nw")
        # Populate the left frame with widgets from a list
        self.alive_flags = []
        self.status_labels = [] 

        # Create the right frame for the scrolled text
        self.right_frame = tk.Frame(self.paned_window, width=(self.root.winfo_width()/5)*4)
        self.right_frame.pack(fill=tk.BOTH, expand=True)
        
        f = Figlet(font='small')
        ascii_art = f.renderText('Galago Tools Manager')


        # Add the right frame to the paned window
        self.paned_window.add(self.left_frame, weight=1)
        self.paned_window.add(self.right_frame, weight=10)
        self.log_files_modified_times = {}
        self.log_files_last_read_positions = {}

        self.output_text = ScrolledText(self.right_frame, state='disabled', wrap='word')
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.tag_config('error', foreground='red') 
        self.output_text.tag_config('warning', foreground='orange')

        self.update_interval = 100
        self.update_log_text()
        self.log_text("------------------------------------------------------------------------------")
        self.log_text(ascii_art)
        self.log_text("------------------------------------------------------------------------------")
        self.log_text("\n")
        self.log_text(f"Log directory: {self.log_folder}")

        # Add search and filter features
        self.search_frame = ttk.Frame(self.right_frame)
        self.search_frame.pack(fill=tk.X, padx=5, pady=5)

        self.search_entry = ttk.Entry(self.search_frame)
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.search_button = ttk.Button(self.search_frame, text="Search", command=self.search_logs)
        self.search_button.pack(side=tk.LEFT)

        self.filter_var = tk.StringVar(value="ALL")
        self.filter_menu = ttk.OptionMenu(self.search_frame, self.filter_var, "ALL", "ALL", "INFO", "DEBUG", "WARNING", "ERROR", command=self.filter_logs)
        self.filter_menu.pack(side=tk.LEFT)
        
        self.clear_button = ttk.Button(self.search_frame, text="Clear Logs", command=self.clear_logs)
        self.clear_button.pack(side=tk.LEFT, padx=(5, 0))

    def kill_all_processes(self) ->None:
        for proc_key, process in self.server_processes.items():
            try:
                self.kill_by_process_id(process.pid)
                time.sleep(0.28)
                logging.info(f"Killed process {process.pid}")
                self.log_text(f"Killed process {process.pid}")
                del process
            except ProcessLookupError as e:
                logging.error(f"failed to shut down process. Error={str(e)}")
                self.log_text(f"failed to shut down process. Error={str(e)}")
                pass
        self.server_processes.clear()
        self.force_kill_tool()
    
    def set_icon(self) -> None:
        if os.name == "nt":
            self.root.iconbitmap(join(ROOT_DIR,"tools","favicon.ico"))
        elif os.name == "posix":
            icon_file = join(ROOT_DIR,"tools","site_logo.png")
            icon_img = tk.Image("photo", file=icon_file)
            if icon_img:
                self.root.iconphoto(True, str(icon_img))      
    
    def update_buttons(self) -> None:
        for button_key, (button_name, button, status_indicator) in self.tool_buttons.items():
            if button_key in self.server_processes:
                process = self.server_processes[button_key]
                is_alive = process is not None and process.poll() is None
            else:
                is_alive = False

            if is_alive:
                status_indicator.itemconfig('status', fill='green')
                button.config(text='Disconnect')
            else:
                status_indicator.itemconfig('status', fill='red')
                button.config(text='Connect')

        self.root.after(500, self.update_buttons)
    
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
            
    def update_log_text(self) -> None:
        try:
            self.output_text.config(state='normal')
            current_scroll = self.output_text.yview()
            for file_name, update_time in self.log_files_modified_times.items():
                last_updated = os.path.getmtime(file_name)
                if update_time is None or last_updated != update_time:
                    last_lines = self.read_last_lines(file_name, 100)
                    self.log_files_modified_times[file_name] = last_updated
                    filter_type = self.filter_var.get()
                    for line in last_lines:
                        if filter_type == "ALL" or f"| {filter_type} |" in line:
                            if "| ERROR |" in line:
                                self.log_text(line.strip(), "error")
                            elif "| WARNING |" in line:
                                self.log_text(line.strip(), "warning")
                            else:
                                self.log_text(line.strip())
            
            if current_scroll == (0.0, 1.0):  # Only scroll to the bottom if at the bottom
                self.output_text.see(tk.END)

            self.output_text.config(state='disabled')
        except FileNotFoundError:
            self.output_text.config(state='disabled')
        except Exception:
            self.output_text.config(state='disabled')
        self.root.after(self.update_interval, self.update_log_text)

    def search_logs(self) -> None:
        search_term = self.search_entry.get().lower()
        self.output_text.tag_remove("search", "1.0", tk.END)
        if search_term:
            start_pos = "1.0"
            while True:
                start_pos = self.output_text.search(search_term, start_pos, stopindex=tk.END, nocase=True)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_term)}c"
                self.output_text.tag_add("search", start_pos, end_pos)
                start_pos = end_pos
            self.output_text.tag_config("search", background="yellow")

    def filter_logs(self, *args: Any) -> None:
        filter_type = self.filter_var.get()
        
        # Clear existing items in the Text widget
        self.output_text.delete("1.0", tk.END)
        
        for file_name in self.log_files_modified_times.keys():
            try:
                with open(file_name, 'r') as file:
                    for line in file:
                        if filter_type == "ALL" or f"| {filter_type} |" in line:
                            if "| ERROR |" in line:
                                self.log_text(line.strip(), "error")
                            elif "| WARNING |" in line:
                                self.log_text(line.strip(), "warning")
                            else:
                                self.log_text(line.strip())
            except Exception as e:
                # Insert error as a new line in the Text widget
                current_time = time.strftime('%Y-%m-%d %H:%M:%S')
                self.output_text.insert(tk.END, f"{current_time} | ERROR | Failed to read log file: {str(e)}\n", ('error',))
    
    def __del__(self) -> None:
        self.kill_all_processes()
    
    def kill_by_process_id(self, process_id:int) -> None:
        try:
            if os.name == 'nt':
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(process_id)])
            else:
                os.kill(process_id, os_signal.SIGINT)
        except ChildProcessError as e:
            self.log_text(f"Failed to kill child process. Error={e}")
        finally:
            return None

    def run_subprocess(self, tool_type:str, tool_name:str, port:int,confirm_modal:bool=False) -> None:
        if confirm_modal:
            box_result = messagebox.askquestion(title="Confirm Tool Restart", message=f"Are you sure you want to restart {tool_name}-{tool_type}")
            if box_result == 'no':
                return None
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
                if self.log_folder:
                    output_file = join(self.log_folder, str(tool_name)) + ".log"
                    process = subprocess.Popen(cmd, stdout=open(output_file,'w'), stderr=subprocess.STDOUT,  universal_newlines=True)
                else:
                     process = subprocess.Popen(cmd, shell=use_shell,universal_newlines=True)
                self.server_processes[tool_name] = process
                self.log_files_modified_times[output_file] = os.path.getmtime(output_file)
            else:
                self.log_text(f"Port {port} for {tool_name} is already occupied. kill process if you want to use this tool", "warning")
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
    
    def log_text(self, text: str, log_type: str = "info") -> None:
        self.output_text.config(state='normal')
        if log_type == "error":
            self.output_text.insert(tk.END, text + "\n", ('error',))
        elif log_type == "warning":
            self.output_text.insert(tk.END, text + "\n", ('warning',))
        else:
            self.output_text.insert(tk.END, text + "\n")
        self.output_text.config(state='disabled')
        self.output_text.see(tk.END)

    def populate_tool_buttons(self) -> None:
        left_width = 300  # Initial width of the left frame

        # Clear existing tool buttons and widgets in the frame
        for widget in self.widgets_frame.winfo_children():
            widget.destroy()

        # Reset tool button state
        self.tool_buttons.clear()
        self.tool_buttons_previous_states.clear()

        def create_tool_frame(parent: tk.Widget, tool_name: str, command: Callable) -> None:
            frame = tk.Frame(parent)
            frame.pack(fill=tk.X, padx=3, pady=2)
            
            label = ttk.Label(frame, text=tool_name, anchor='w')
            label.pack(side=tk.LEFT, padx=(5, 10), pady=5, expand=True, fill=tk.X)
            
            # Changed from Frame to Canvas
            status_indicator = tk.Canvas(frame, width=12, height=12, highlightthickness=0)
            status_indicator.pack(side=tk.LEFT, padx=(0, 10), pady=5)
            status_indicator.create_oval(2, 2, 10, 10, fill='red', tags='status')
            
            button = tk.Button(frame, text="Connect", command=command, width=10)
            button.pack(side=tk.RIGHT, padx=(5, 5), pady=5)
            
            self.tool_buttons[tool_name] = (tool_name, button, status_indicator)
            self.tool_buttons_previous_states[tool_name] = False

        # Tool Box
        create_tool_frame(self.widgets_frame, "Tool Box", self.start_toolbox)

        # Workcell tools
        if self.config.workcell_config:
            for t in self.config.workcell_config.tools:
                try:
                    create_tool_frame(
                        self.widgets_frame,
                        t.name,
                        lambda t=t: self.run_subprocess(t.type, t.name, t.port, True, )
                    )
                except Exception as e:
                    logging.error(f"Failed to add button {t.id}. Error is {e}")

        # Restart All button
        restart_frame = ttk.Frame(self.widgets_frame)
        restart_frame.pack(fill=tk.X, padx=3, pady=4)
        restart_all_button = ttk.Button(restart_frame, text="Restart All", command=self.run_all_tools)
        restart_all_button.pack(fill=tk.X)

        # Add this line to ensure the widgets_frame fits its contents
        self.widgets_frame.update_idletasks()
        self.left_canvas.config(width=self.widgets_frame.winfo_reqwidth())

        # Set the initial position of the paned window sash
        self.paned_window.sashpos(0, left_width)


    def force_kill_tool(self) -> None:
        try:
            if os.name != 'nt':
                subprocess.Popen("lsof -t -i tcp:1010 | xargs kill", shell=True)
        except Exception as e:
            self.log_text(f"Failed to kill web app. Error={e}")
    

    def start_toolbox(self) -> None:
        try:
            self.run_subprocess("toolbox", "Tool Box",1010,False)
        except subprocess.CalledProcessError:
            logging.info("There was an error launching toolbox server.")

    def run_all_tools(self) -> None:
        self.kill_all_processes()
        time.sleep(0.5)
        self.load_tools()
        self.start_toolbox()

        counter = 0
        self.populate_tool_buttons()

        if self.config.workcell_config is None:
            logging.error("No workcell configuration loaded")
            return

        for t in self.config.workcell_config.tools:
            logging.info(f"Launching process for tool {t.name}")
            counter+=1
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
        self.update_buttons()

    def on_closing(self) -> None:
        logging.info("Calling on closing function")
        try:
           self.kill_all_processes()
        except Exception as e: 
            self.log_text(f"Failed to kill tool servers, {e}")
        finally:
            self.log_text("Closing Galago Manager")
            time.sleep(2)
            self.root.destroy()

    def show_gui(self) -> None:
        process_thread = threading.Thread(target=self.run_all_tools)
        process_thread.daemon = False
        process_thread.start()
        self.root.mainloop()
        
    def clear_logs(self) -> None:
        """Clear all logs from the output text widget"""
        self.output_text.config(state='normal')
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state='disabled')


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
        root = tk.Tk()
        config = Config()
        f = Figlet(font='slant')
        print(f.renderText('Galago Tools Manager'))
        manager = ToolsManager(root, config)
        manager.show_gui()
        return 0
    except Exception:
        logging.exception("Failed to launch tools")
        sys.exit(1)
        return 1

if __name__ == "__main__":
    main()