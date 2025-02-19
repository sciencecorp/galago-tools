import logging.handlers
import subprocess
from tools.app_config import Config
import threading
import socket 
import logging 
import os
import sys
import signal as os_signal
import time
import argparse
from os.path import join, dirname
from typing import Optional, Callable, Dict
import flet as ft
from datetime import datetime

ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))
LOG_TIME = int(time.time())
TOOLS_32BITS = ["vcode","bravo","hig_centrifuge","plateloc","vspin"]

# Configure logging to be less verbose by default
logging.getLogger("flet_core").setLevel(logging.WARNING)  # Reduce Flet framework logging
logging.getLogger("matplotlib").setLevel(logging.WARNING)  # Reduce any matplotlib logging

logging.basicConfig(
    level=logging.INFO,  # Changed from DEBUG to INFO by default
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

class ToolsManager:
    def __init__(self, page: ft.Page, config: Config) -> None:
        self.page = page
        self.page.title = "Galago Tools Manager"
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20
        self.page.window_center = True
        self.page.window_resizable = True
        self.page.window_maximized = True
        self.page.icon = "site_logo.png"  # Reference from assets directory without leading slash

        # Set theme colors
        self.page.theme = ft.Theme(
            color_scheme_seed=ft.colors.TEAL,
            visual_density=ft.ThemeVisualDensity.COMFORTABLE,
        )
        self.page.dark_theme = ft.Theme(
            color_scheme_seed=ft.colors.TEAL,
            visual_density=ft.ThemeVisualDensity.COMFORTABLE,
        )

        # Buffer for batching log updates
        self.log_buffer = []
        self.last_update = time.time()
        self.update_batch_size = 10  # Number of logs to accumulate before updating
        self.min_update_interval = 0.1  # Minimum time between updates in seconds
        self.auto_scroll = False  # Track if we should auto-scroll logs

        self.running_tools = 0
        self.config_file = ""
        logging.info("Starting Galago Manager")
        self.config = config
        working_dir = "" if not config.app_config.data_folder else config.app_config.data_folder
        self.log_folder = os.path.join(working_dir, "data", "trace_logs", str(LOG_TIME))
        self.workcell = config.app_config.workcell

        if not os.path.exists(self.log_folder):
            logging.debug("folder does not exist. creating folder")
            os.makedirs(self.log_folder)

        # Kill any existing tool servers before starting
        self.kill_existing_tool_servers()

        self.server_processes: Dict[str, subprocess.Popen] = {}
        self.tool_box_process: Optional[subprocess.Popen] = None
        self.tool_buttons: Dict[str, tuple[str, ft.ElevatedButton, ft.Container]] = {}
        self.tool_buttons_previous_states: Dict[str, bool] = {}
        self.log_files_modified_times = {}
        self.log_files_last_read_positions = {}
        self.last_log_update = time.time()
        
        # Create main layout
        self.setup_layout()
        self.update_interval = 500  # Increased to 500ms
        self.start_log_update_timer()

    def setup_layout(self) -> None:
        # Create theme toggle button
        theme_toggle = ft.IconButton(
            icon=ft.icons.DARK_MODE,  # Start with moon icon since we start in light mode
            tooltip="Toggle dark mode",
            on_click=self.toggle_theme,
        )
        self.theme_toggle = theme_toggle  # Store reference to update icon later

        # Create main column for the entire layout
        main_column = ft.Column(
            controls=[
                # Main row with tools and logs panels
                ft.Row(
                    spacing=20,
                    controls=[
                        # Left panel for tools
                        ft.Container(
                            width=300,
                            content=ft.Column(
                                scroll=ft.ScrollMode.AUTO,
                                controls=[
                                    ft.Text("Tools", size=24, weight=ft.FontWeight.BOLD),
                                    ft.Divider(),
                                ],
                                spacing=10,
                                horizontal_alignment=ft.CrossAxisAlignment.START,
                            ),
                            bgcolor=ft.colors.SURFACE,
                            border_radius=10,
                            padding=ft.padding.only(left=10, top=10, bottom=10, right=20),
                            border=ft.border.all(1, ft.colors.OUTLINE),
                        ),
                        # Right panel for logs
                        ft.Container(
                            expand=True,
                            content=ft.Column(
                                controls=[
                                    # Search and filter controls
                                    ft.Row(
                                        controls=[
                                            ft.TextField(
                                                expand=True,
                                                hint_text="Search logs...",
                                                on_change=self.search_logs,
                                                border_radius=8,
                                            ),
                                            ft.Dropdown(
                                                width=120,
                                                options=[
                                                    ft.dropdown.Option("ALL"),
                                                    ft.dropdown.Option("INFO"),
                                                    ft.dropdown.Option("DEBUG"),
                                                    ft.dropdown.Option("WARNING"),
                                                    ft.dropdown.Option("ERROR"),
                                                ],
                                                value="ALL",
                                                on_change=self.filter_logs,
                                            ),
                                        ],
                                        spacing=10,
                                    ),
                                    # Log output
                                    ft.Container(
                                        expand=True,
                                        width=float("inf"),
                                        content=ft.Column(
                                            scroll=ft.ScrollMode.ALWAYS,
                                            controls=[],
                                            spacing=4,
                                            expand=True,
                                            width=float("inf"),
                                            on_scroll=self.handle_scroll,
                                        ),
                                        bgcolor=ft.colors.SURFACE_VARIANT,
                                        border_radius=10,
                                        padding=ft.padding.only(left=15, top=15, bottom=15, right=5),
                                        border=ft.border.all(1, ft.colors.OUTLINE),
                                    ),
                                ],
                                spacing=10,
                                expand=True,
                            ),
                            bgcolor=ft.colors.SURFACE,
                            border_radius=10,
                            padding=10,
                            border=ft.border.all(1, ft.colors.OUTLINE),
                        ),
                    ],
                    expand=True,
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                # Theme toggle at the bottom
                ft.Container(
                    content=theme_toggle,
                    padding=ft.padding.only(top=10),
                ),
            ],
            expand=True,
        )
        
        self.page.add(main_column)
        self.log_container = main_column.controls[0].controls[1].content.controls[1]
        self.tools_column = main_column.controls[0].controls[0].content
        self.search_field = main_column.controls[0].controls[1].content.controls[0].controls[0]
        self.filter_dropdown = main_column.controls[0].controls[1].content.controls[0].controls[1]

    def create_tool_button(self, tool_name: str, command: Callable) -> ft.Container:
        status_indicator = ft.Container(
            width=12,
            height=12,
            bgcolor=ft.colors.RED,
            border_radius=6,
        )
        
        def handle_button_click(e: ft.ControlEvent) -> None:
            if tool_name in self.server_processes and self.server_processes[tool_name] is not None:
                # If process is running, kill it
                self.kill_process_by_name(tool_name)
            else:
                # If process is not running, start it
                command()
            self.page.update()  # Ensure UI updates after action
        
        button = ft.ElevatedButton(
            text="Connect",
            on_click=handle_button_click,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            width=100,  # Fixed width for consistency
        )
        
        tool_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(tool_name, expand=True),
                    status_indicator,
                    button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=10,  # Added spacing between elements
            ),
            padding=ft.padding.only(left=10, top=5, bottom=5, right=5),  # Adjusted padding
            bgcolor=ft.colors.SURFACE,  # Theme-aware background color
            border_radius=8,
            border=ft.border.all(1, ft.colors.OUTLINE),  # Theme-aware border color
        )
        
        self.tool_buttons[tool_name] = (tool_name, button, status_indicator)
        return tool_row

    def populate_tool_buttons(self) -> None:
        # Keep header elements
        self.tools_column.controls = [self.tools_column.controls[0], self.tools_column.controls[1]]
        
        # Add Tool Box button
        self.tools_column.controls.append(
            self.create_tool_button("Tool Box", self.start_toolbox)
        )
        
        # Add workcell tools
        if self.config.workcell_config:
            for t in self.config.workcell_config.tools:
                try:
                    # Store tool info in a closure to avoid late binding issues
                    def make_tool_command(tool_type: str = t.type, tool_name: str = t.name, tool_port: int = t.port) -> Callable[[], None]:
                        return lambda: self._run_subprocess_impl(tool_type, tool_name, tool_port)
                    
                    self.tools_column.controls.append(
                        self.create_tool_button(
                            t.name,
                            make_tool_command()
                        )
                    )
                except Exception as e:
                    logging.error(f"Failed to add button {t.id}. Error is {e}")
        
        # Add Restart All button
        self.tools_column.controls.append(
            ft.ElevatedButton(
                text="Restart All",
                on_click=lambda _: self.run_all_tools(),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    bgcolor=ft.colors.TEAL,
                    color=ft.colors.WHITE,
                ),
                width=270,  # Match width of tool containers (300 - left/right padding)
            )
        )

    def toggle_theme(self, e: ft.ControlEvent) -> None:
        is_dark_mode = self.page.theme_mode == ft.ThemeMode.DARK
        self.page.theme_mode = ft.ThemeMode.LIGHT if is_dark_mode else ft.ThemeMode.DARK
        # Update the icon based on the new theme - show sun in dark mode, moon in light mode
        self.theme_toggle.icon = ft.icons.DARK_MODE if is_dark_mode else ft.icons.LIGHT_MODE
        self.theme_toggle.tooltip = "Toggle light mode" if is_dark_mode else "Toggle dark mode"
        self.page.update()

    def handle_scroll(self, e: ft.OnScrollEvent) -> None:
        # Check if we're at the bottom of the scroll
        if e.pixels is None or e.max_scroll_extent is None:
            self.auto_scroll = True
            return
        
        # If we're within 20 pixels of the bottom, enable auto-scroll
        self.auto_scroll = abs(e.pixels - e.max_scroll_extent) < 20

    def log_text(self, text: str, log_type: str = "info") -> None:
        # Parse timestamp and message
        try:
            # Try to split timestamp and message
            full_timestamp, level, *message_parts = text.split(" | ")
            # Convert timestamp to shorter format (HH:MM:SS)
            try:
                dt = datetime.strptime(full_timestamp, '%Y-%m-%d %H:%M:%S')
                timestamp = dt.strftime('%H:%M:%S')
            except ValueError:
                timestamp = full_timestamp
            message = " | ".join(message_parts)
        except ValueError:
            # If splitting fails, use the whole text as message
            timestamp = datetime.now().strftime('%H:%M:%S')
            message = text
            level = "INFO"

        # Set colors based on log type and theme
        colors = {
            "error": ft.colors.RED_400,
            "warning": ft.colors.ORANGE_400,
            "info": ft.colors.ON_SURFACE,
            "debug": ft.colors.ON_SURFACE_VARIANT,
        }
        
        # Create the log entry
        log_entry = ft.Column(
            controls=[
                ft.Divider(height=1, color=ft.colors.OUTLINE),
                ft.Text(
                    f"{timestamp} | {level} | {message}",
                    size=14,
                    color=colors.get(log_type.lower(), colors["info"]),
                    selectable=True,
                    no_wrap=False,
                ),
            ],
            spacing=0,
        )
        
        self.log_container.content.controls.append(log_entry)
        if len(self.log_container.content.controls) > 1000:
            self.log_container.content.controls = self.log_container.content.controls[-1000:]

        # Only update if enough time has passed
        current_time = time.time()
        if current_time - self.last_log_update >= 0.5:  # Update at most every 500ms
            # Only auto-scroll if we were already at the bottom
            if self.auto_scroll:
                self.log_container.content.scroll_to(offset=float('inf'), duration=100)
            self.log_container.update()
            self.last_log_update = current_time

    def search_logs(self, e: ft.ControlEvent) -> None:
        search_term = self.search_field.value.lower()
        for log_entry in self.log_container.content.controls:
            if isinstance(log_entry, ft.Column) and len(log_entry.controls) > 1:
                text_control = log_entry.controls[1]  # Get the Text control (index 1 after divider)
                log_entry.visible = (not search_term) or (search_term in text_control.value.lower())
        self.page.update()

    def filter_logs(self, e: ft.ControlEvent) -> None:
        filter_type = self.filter_dropdown.value
        self.log_container.content.controls.clear()
        
        for file_name in self.log_files_modified_times.keys():
            try:
                with open(file_name, 'r') as file:
                    lines = file.readlines()
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        if filter_type == "ALL":
                            if "| ERROR |" in line:
                                self.log_text(line, "error")
                            elif "| WARNING |" in line:
                                self.log_text(line, "warning")
                            else:
                                self.log_text(line)
                        elif f"| {filter_type} |" in line:
                            log_type = filter_type.lower()
                            self.log_text(line, log_type)
            except Exception as e:
                current_time = datetime.now().strftime('%H:%M:%S')
                self.log_text(f"{current_time} | ERROR | Failed to read log file: {str(e)}", "error")
        
        self.page.update()

    def update_buttons(self) -> None:
        while True:
            try:
                for button_key, (_, button, status_indicator) in self.tool_buttons.items():
                    if button_key in self.server_processes:
                        process = self.server_processes[button_key]
                        is_alive = process is not None and process.poll() is None
                    else:
                        is_alive = False

                    status_indicator.bgcolor = ft.colors.GREEN if is_alive else ft.colors.RED
                    button.text = "Disconnect" if is_alive else "Connect"
                
                self.page.update()
            except Exception as e:
                logging.error(f"Error in update_buttons: {e}")
            time.sleep(0.5)  # Update every 500ms

    def start_log_update_timer(self) -> None:
        def update_logs() -> None:
            while True:
                try:
                    new_logs = []
                    for file_name, update_time in self.log_files_modified_times.items():
                        last_updated = os.path.getmtime(file_name)
                        if update_time is None or last_updated != update_time:
                            last_lines = self.read_last_lines(file_name, 100)
                            self.log_files_modified_times[file_name] = last_updated
                            filter_type = self.filter_dropdown.value
                            
                            # Collect all new logs before updating UI
                            for line in last_lines:
                                line = line.strip()
                                if not line:
                                    continue
                                if filter_type == "ALL" or f"| {filter_type} |" in line:
                                    if "| ERROR |" in line:
                                        new_logs.append((line, "error"))
                                    elif "| WARNING |" in line:
                                        new_logs.append((line, "warning"))
                                    else:
                                        new_logs.append((line, "info"))
                    
                    # Update UI with all new logs at once
                    if new_logs:
                        for line, log_type in new_logs:
                            self.log_text(line, log_type)
                                
                except Exception as e:
                    logging.error(f"Error updating logs: {e}")
                
                time.sleep(self.update_interval / 1000)
        
        # Start update threads
        button_thread = threading.Thread(target=self.update_buttons, daemon=True)
        log_thread = threading.Thread(target=update_logs, daemon=True)
        button_thread.start()
        log_thread.start()

    def kill_all_processes(self) -> None:
        logging.info("Killing all tool processes")
        # Create a copy of the keys since we'll be modifying the dict
        process_keys = list(self.server_processes.keys())
        for proc_key in process_keys:
            try:
                process = self.server_processes[proc_key]
                self.kill_by_process_id(process.pid)
                time.sleep(0.5)
                logging.info(f"Killed process {process.pid}")
                self.log_text(f"Killed process {process.pid}")
                del self.server_processes[proc_key]  # Remove from dict after killing
            except ProcessLookupError as e:
                logging.error(f"Failed to shut down process {proc_key}. Error={str(e)}")
                self.log_text(f"Failed to shut down process {proc_key}. Error={str(e)}")
                # Still remove from dict if we can't find the process
                if proc_key in self.server_processes:
                    del self.server_processes[proc_key]
            except Exception as e:
                logging.error(f"Error killing process {proc_key}: {str(e)}")
                if proc_key in self.server_processes:
                    del self.server_processes[proc_key]

    def kill_by_process_id(self, process_id: int) -> None:
        try:
            if os.name == 'nt':
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(process_id)])
            else:
                os.kill(process_id, os_signal.SIGINT)
        except ChildProcessError as e:
            logging.error(f"Failed to kill child process {process_id}. Error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error killing process {process_id}: {e}")
        finally:
            return None

    def run_subprocess(self, tool_type: str, tool_name: str, port: int, confirm_modal: bool = False) -> None:
        if confirm_modal:
            def handle_confirm(e: ft.ControlEvent) -> None:
                if e.control.data:
                    self._run_subprocess_impl(tool_type, tool_name, port)
                dlg.open = False
                self.page.update()

            dlg = ft.AlertDialog(
                title=ft.Text("Confirm Tool Restart"),
                content=ft.Text(f"Are you sure you want to restart {tool_name}-{tool_type}?"),
                actions=[
                    ft.TextButton("Yes", on_click=handle_confirm, data=True),
                    ft.TextButton("No", on_click=handle_confirm, data=False),
                ],
            )
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()
        else:
            self._run_subprocess_impl(tool_type, tool_name, port)

    def _run_subprocess_impl(self, tool_type: str, tool_name: str, port: int) -> None:
        try:
            # First kill any existing process
            self.kill_process_by_name(str(tool_name))
            
            tool_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = tool_socket.connect_ex(('127.0.0.1', int(port)))
            tool_socket.close()  # Make sure to close the socket
            
            if result != 0:
                cmd = self.get_shell_command(tool_type=tool_type, port=port)
                os.chdir(ROOT_DIR)
                use_shell = False
                if os.name == 'nt':
                    use_shell = True
                    
                if self.log_folder:
                    output_file = join(self.log_folder, str(tool_name)) + ".log"
                    process = subprocess.Popen(cmd, stdout=open(output_file,'w'), stderr=subprocess.STDOUT, universal_newlines=True)
                else:
                    process = subprocess.Popen(cmd, shell=use_shell, universal_newlines=True)
                
                self.server_processes[tool_name] = process
                
                # Only add to log files if the file exists
                if self.log_folder:
                    output_file = join(self.log_folder, str(tool_name)) + ".log"
                    if os.path.exists(output_file):
                        self.log_files_modified_times[output_file] = os.path.getmtime(output_file)
            else:
                logging.warning(f"Port {port} for {tool_name} is already occupied")
        except subprocess.CalledProcessError as e:
            logging.error(f"CalledProcessError starting {tool_name}: {str(e)}")
        except Exception as e:
            logging.error(f"Error starting {tool_name}: {str(e)}")

    def get_shell_command(self, tool_type: str, port: int) -> list:
        python_cmd: str = f"python -m tools.{tool_type}.server --port={port}"
        if os.name == 'nt':
            return ["cmd.exe", "/C", python_cmd]       
        else:
            return python_cmd.split()

    def kill_process_by_name(self, process_name: str) -> None:
        if process_name not in self.server_processes.keys():
            return None
        else:
            try:
                process = self.server_processes[process_name]
                process_id = process.pid
                self.kill_by_process_id(process_id)
                del self.server_processes[process_name]  # Remove from tracking
            except Exception as e:
                logging.error(f"Failed to kill process {process_name}. Error: {str(e)}")
                # Still try to remove from tracking
                if process_name in self.server_processes:
                    del self.server_processes[process_name]
        return None

    def start_toolbox(self) -> None:
        logging.info("Launching Toolbox")
        try:
            self.run_subprocess("toolbox", "Tool Box", 1010, False)
        except subprocess.CalledProcessError:
            logging.info("There was an error launching toolbox server.")

    def run_all_tools(self) -> None:
        # First kill all processes
        self.kill_all_processes()
        time.sleep(0.5)
        
        # Reload configs
        self.config.load_app_config()
        self.load_tools()
        
        # Clear existing buttons and recreate them
        self.populate_tool_buttons()
        self.page.update()
        
        # Start toolbox first
        self.start_toolbox()
        time.sleep(0.5)

        if self.config.workcell_config is None:
            logging.error("No workcell configuration loaded")
            return

        # Start all tools
        for t in self.config.workcell_config.tools:
            logging.info(f"Launching process for tool {t.name}")
            tool_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = tool_socket.connect_ex(('127.0.0.1', t.port))
            if result != 0:
                try:
                    self.run_subprocess(t.type, t.name, t.port, False)
                except Exception as e:
                    logging.error(f"Failed to launch tool {t.name}. Error is {e}")
            else:
                logging.warning(f"Port for tool {t.name} is already occupied")
            time.sleep(0.1)  # Small delay between starting tools
        
        # Start button update thread
        button_thread = threading.Thread(target=self.update_buttons, daemon=True)
        button_thread.start()

    def load_tools(self) -> None:
        self.config.load_workcell_config()

    def read_last_lines(self, filename: str, lines: int = 100) -> list[str]:
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

    def kill_existing_tool_servers(self) -> None:
        """Kill any existing tool server processes at startup."""
        logging.info("Checking for existing tool servers...")
        if os.name == 'nt':
            # Windows implementation
            try:
                # Get all Python processes
                output = subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq python.exe']).decode()
                for line in output.split('\n'):
                    if 'tools.' in line and 'server' in line:
                        pid = int(line.split()[1])
                        subprocess.call(['taskkill', '/F', '/PID', str(pid)])
            except Exception as e:
                logging.error(f"Error killing existing Windows processes: {e}")
        else:
            # Unix/Mac implementation
            try:
                # Get all Python processes
                ps_output = subprocess.check_output(['ps', 'aux']).decode()
                for line in ps_output.split('\n'):
                    if 'python' in line and 'tools.' in line and 'server' in line:
                        try:
                            # Extract PID (second column in ps aux output)
                            pid = int(line.split()[1])
                            os.kill(pid, os_signal.SIGTERM)
                            time.sleep(0.1)  # Give process time to terminate
                            try:
                                # Check if process still exists
                                os.kill(pid, 0)
                                # If we get here, process still exists, force kill
                                os.kill(pid, os_signal.SIGKILL)
                            except OSError:
                                # Process is already gone
                                pass
                        except (ValueError, ProcessLookupError) as e:
                            logging.warning(f"Could not kill process from line: {line}. Error: {e}")
            except Exception as e:
                logging.error(f"Error killing existing Unix processes: {e}")
        logging.info("Finished checking for existing tool servers")

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
        # Even in debug mode, keep UI framework logging minimal
        logging.getLogger("flet_core").setLevel(logging.WARNING)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    try:
        logging.info("Starting Galago Tools Manager")
        config = Config()
        logging.info("Loading app config")
        config.load_app_config()
        logging.info("Loading workcell config")
        config.load_workcell_config()
        
        def main_window(page: ft.Page) -> None:
            manager = ToolsManager(page, config)
            manager.populate_tool_buttons()
            manager.run_all_tools()
        
        # Always use assets directory for consistent icon loading
        ft.app(target=main_window, assets_dir=join(ROOT_DIR, "tools"))
        return 0
    except Exception:
        logging.exception("Failed to launch tools")
        sys.exit(1)
        return 1

if __name__ == "__main__":
    main()