import asyncio
import websockets
import json
import logging
import logging.handlers
import os
import sys
import subprocess
import socket
import signal as os_signal
import time
from pathlib import Path
from typing import Dict, Set, Optional, Tuple, List, Any
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from tools.app_config import Config
from tools.utils import get_shell_command, get_local_ip
import webbrowser
import appdirs #type: ignore
import requests
from packaging import version
from tools import __version__ as galago_version


# Add the project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Configuration flags - matching ToolsManager
USE_APP_DATA_DIR = True  # Set to False for local development/testing

# Use appdirs to get platform-specific data directory
APP_NAME = "galago"
APP_AUTHOR = "sciencecorp"
DATA_DIR = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)

LOG_TIME = int(time.time())
LOCAL_IP = get_local_ip()

def setup_logging() -> Path:
    """Setup logging similar to ToolsManager"""
    # Set appropriate log directory based on configuration
    if USE_APP_DATA_DIR:
        # Use platform-specific app data directory (for production)
        log_folder = Path(DATA_DIR) / "trace_logs" / str(LOG_TIME)
    else:
        # Use directory relative to ROOT_DIR (for local development/testing)
        log_folder = ROOT_DIR / "data" / "trace_logs" / str(LOG_TIME)

    # Ensure the log directory exists
    try:
        log_folder.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Failed to create log directory: {log_folder}. Error: {str(e)}")
        log_folder = Path.home() / "galago_logs" / str(LOG_TIME)
        log_folder.mkdir(parents=True, exist_ok=True)

    # Setup logging configuration
    log_file = log_folder / "web_server.log"
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    root_logger = logging.getLogger()
    root_logger.handlers.clear()  

    # Setup file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)  
    
    # Setup console handler - only INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Configure root logger
    root_logger.setLevel(logging.INFO)  
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return log_folder

def check_for_updates() -> Tuple[bool, str, str]:
    """Check if there's a newer version of galago-tools on PyPI"""
    try:
        current_version = galago_version
        response = requests.get("https://pypi.org/pypi/galago-tools/json", timeout=3)
        if response.status_code == 200:
            data = response.json()
            latest_version = data["info"]["version"]
            
            # Compare versions using packaging.version for proper semantic versioning comparison
            if version.parse(latest_version) > version.parse(current_version):
                logging.info(f"Update available: {current_version} -> {latest_version}")
                return True, current_version, latest_version
            else:
                logging.info(f"Using latest version: {current_version}")
                return False, current_version, latest_version
    except Exception as e:
        logging.warning(f"Failed to check for updates: {str(e)}")
    
    # Return default values if the check fails
    return False, galago_version, galago_version

def display_startup_message(log_folder: Path, update_available: bool = False, current_version: str = "", latest_version: str = "") -> None:
    """Display startup message matching the tkinter ToolsManager format"""
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Print to console - keep it simple like tkinter version
    print("=" * 80)
    print("🚀 🤖 GALAGO WEB SERVER STARTED")
    print("=" * 80)
    print("")
    print(f"📦 Version: {galago_version}")
    if update_available:
        print(f"    A new version ({latest_version}) is available!")
        print("    Upgrade using: pip install --upgrade galago-tools")
    print(f"⏰ Started: {current_time}")
    print(f"🆔 Session: {LOG_TIME}")
    print(f"💻 Platform: {os.name}")
    print("")
    print("📂 URLs:")
    print(f"   Tool Server IP: {LOCAL_IP}")
    print("   Web Interface Local: http://localhost:8080/")
    print(f"   Web Interface On Network: http://{LOCAL_IP}:8080/")
    print(f"   Logs Directory: {log_folder}")
    print("")
    print("✅ Web Server initialized successfully")
    print("🔄 Starting WebSocket and HTTP servers...")
    print("-" * 80)
    print("")

# Global state
connected_clients: Set[Any] = set()
server_processes: Dict[str, subprocess.Popen] = {}
config: Optional[Config] = None
log_folder: Optional[Path] = None
log_positions: Dict[str, int] = {}
last_tool_status: Dict[str, str] = {}
logger = logging.getLogger(__name__)

def is_process_running(tool_name: str) -> bool:
    """Check if a process is running"""
    if tool_name not in server_processes:
        return False
    process = server_processes[tool_name]
    return process is not None and process.poll() is None

def is_port_occupied(port: int) -> bool:
    """Check if a port is occupied"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('127.0.0.1', port))
            return result == 0
    except Exception:
        return False

def open_browser(url: str, delay: float = 2.0) -> None:
    """Open browser after a delay to ensure server is ready"""
    def delayed_open() -> None:
        time.sleep(delay)
        try:
            # Try to verify the server is responding before opening browser
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    import urllib.request
                    urllib.request.urlopen(url, timeout=1)
                    break
                except Exception as e:
                    if attempt < max_attempts - 1:
                        time.sleep(0.5)
                    else:
                        logger.warning(f"Server not responding at {url} after {max_attempts} attempts: {e}")
            
            logger.info(f"Opening browser to {url}")
            webbrowser.open(url)
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")
            logger.info(f"Please manually open: {url}")
    
    thread = threading.Thread(target=delayed_open, daemon=True)
    thread.start()

def kill_by_process_id(process_id: int) -> None:
    """Kill a process by PID"""
    try:
        if os.name == 'nt':
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(process_id)])
        else:
            os.kill(process_id, os_signal.SIGTERM)
            time.sleep(0.5)
            try:
                os.kill(process_id, os_signal.SIGINT)
            except ProcessLookupError:
                pass
        logger.info(f"Killed process {process_id}")
    except Exception as e:
        logger.error(f"Failed to kill process {process_id}: {e}")

def kill_process_by_name(process_name: str) -> None:
    """Kill a process by name"""
    if process_name not in server_processes:
        return
    try:
        process = server_processes[process_name]
        kill_by_process_id(process.pid)
        del server_processes[process_name]
        logger.info(f"Killed process {process_name}")
    except Exception as e:
        logger.warning(f"Failed to kill process {process_name}: {e}")

async def get_tool_status() -> List[Dict[str, Any]]:
    """Get current status of all tools"""
    tools_status: List[Dict[str, Any]] = []
    
    # Add toolbox
    toolbox_running = is_process_running("Tool Box")
    tools_status.append({
        "name": "Tool Box",
        "type": "toolbox",
        "port": 1010,
        "status": "running" if toolbox_running else "stopped",
        "image": "toolbox.png"
    })
    
    # Add workcell tools
    if config and config.workcell_config:
        for tool in config.workcell_config.tools:
            tool_running = is_process_running(tool.name)
            tools_status.append({
                "name": tool.name,
                "type": tool.type,
                "port": tool.port,
                "status": "running" if tool_running else "stopped",
                "image": f"{tool.type}.png"
            })
    
    return tools_status

async def reload_config() -> bool:
    """Reload the configuration from disk"""
    global config, last_tool_status
    
    try:
        logger.info("Reloading configuration...")
        config = Config()
        config.load_workcell_config()
        
        # Reset status tracking to force update
        last_tool_status = {}
        
        logger.info("Configuration reloaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        return False

async def relaunch_all_tools() -> bool:
    """Stop all tools, reload config, then start all tools"""
    try:
        logger.info("Starting tool relaunch sequence...")
        
        # Step 1: Stop all running tools
        current_tools = await get_tool_status()
        running_tools = [tool for tool in current_tools if tool['status'] == 'running']
        
        if running_tools:
            logger.info(f"Stopping {len(running_tools)} running tools...")
            for tool in running_tools:
                await stop_tool(tool['name'])
            
            # Wait for all tools to stop
            await asyncio.sleep(2)
        
        # Step 2: Reload configuration
        config_success = await reload_config()
        if not config_success:
            raise Exception("Failed to reload configuration")
        
        # Step 3: Start all tools from new config
        logger.info("Starting all tools with new configuration...")
        new_tools = await get_tool_status()
        
        start_tasks = []
        for tool in new_tools:
            if tool['name'] != 'Tool Box':  # Skip toolbox if you don't want to auto-start it
                start_tasks.append(start_tool(tool['name'], tool['type'], tool['port']))
        
        # Start all tools concurrently but with small delays
        for i, task in enumerate(start_tasks):
            await asyncio.sleep(0.5 * i)  # Stagger starts
            asyncio.create_task(task)
        
        logger.info("Tool relaunch sequence completed")
        return True
        
    except Exception as e:
        logger.error(f"Failed to relaunch tools: {e}")
        return False

async def check_for_status_changes() -> None:
    """Check if tool status has changed and broadcast updates"""
    global last_tool_status
    
    current_status = await get_tool_status()
    
    # Convert to dict for easier comparison
    current_status_dict = {tool['name']: tool['status'] for tool in current_status}
    
    # Check if status has changed
    if current_status_dict != last_tool_status:
        await send_tool_status()
        last_tool_status = current_status_dict.copy()

async def monitor_tool_processes() -> None:
    """Monitor tool processes and broadcast status changes"""
    logger.info("Starting tool process monitoring")
    
    while True:
        try:
            await check_for_status_changes()
        except Exception as e:
            logger.error(f"Error in process monitoring: {e}")
        
        await asyncio.sleep(2)  # Check every 2 seconds

async def start_tool(tool_name: str, tool_type: str, port: int) -> bool:
    """Start a tool process with improved logging"""
    try:
        kill_process_by_name(tool_name)
        
        if is_port_occupied(port):
            raise Exception(f"Port {port} is already occupied")
        
        cmd = get_shell_command(tool_type=tool_type, port=port)
        os.chdir(ROOT_DIR)
        
        if log_folder:
            log_file = log_folder / f"{tool_name}.log"
            
            # Initialize log position tracking before starting the process
            log_positions[str(log_file)] = 0
            
            # Create the log file first and add an initial entry
            with open(log_file, 'w') as f:
                f.write(f"Starting {tool_name} ({tool_type}) on port {port}\n")
                f.flush()  # Force immediate write
            
            # Open log file for subprocess with line buffering
            log_handle = open(log_file, 'a', buffering=1)  # Line buffered
            
            process = subprocess.Popen(
                cmd,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                shell=os.name == 'nt',
                bufsize=1  # Line buffered
            )
            
            # Store the file handle so we can close it later
            if not hasattr(process, '_log_handles'):
                setattr(process, '_log_handles', [])
            getattr(process, '_log_handles').append(log_handle)
            
        else:
            process = subprocess.Popen(
                cmd,
                universal_newlines=True,
                shell=os.name == 'nt'
            )
        
        server_processes[tool_name] = process
        logger.info(f"Started {tool_name} on port {port}")
        
        # Immediately check for new logs after a brief delay
        asyncio.create_task(immediate_log_check(tool_name))
        
        # Schedule a status check after a brief delay to catch the change
        asyncio.create_task(delayed_status_check())
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to start {tool_name}: {e}")
        return False

async def stop_tool(tool_name: str) -> bool:
    """Stop a tool process with proper cleanup"""
    try:
        if tool_name in server_processes:
            process = server_processes[tool_name]
            
            # Close any open log file handles
            if hasattr(process, '_log_handles'):
                for handle in process._log_handles:
                    try:
                        handle.close()
                    except Exception as e:
                        logger.warning(f"Error closing log file {handle.name}: {e}")
        
        kill_process_by_name(tool_name)
        logger.info(f"Stopped {tool_name}")
        
        # Schedule a status check after a brief delay to catch the change
        asyncio.create_task(delayed_status_check())
        
        return True
    except Exception as e:
        logger.error(f"Failed to stop {tool_name}: {e}")
        return False

async def delayed_status_check() -> None:
    """Check status after a brief delay"""
    await asyncio.sleep(1)
    await check_for_status_changes()

async def get_recent_logs(lines: int = 100) -> List[Dict[str, Any]]:
    """Get recent logs from all log files"""
    logs: List[Dict[str, Any]] = []
    
    if not log_folder:
        return logs
        
    try:
        for log_file_path in log_folder.glob("*.log"):
            try:
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    file_lines = f.readlines()
                    recent_lines = file_lines[-lines:] if len(file_lines) > lines else file_lines
                    
                    for line in recent_lines:
                        logs.append({
                            "source": log_file_path.stem,
                            "content": line.strip(),
                            "timestamp": time.time()
                        })
            except Exception as e:
                logger.error(f"Error reading log file {log_file_path}: {e}")
    except Exception as e:
        logger.error(f"Error accessing log folder: {e}")
    
    logs.sort(key=lambda x: x['timestamp'], reverse=True)
    return logs[:lines]

async def immediate_log_check(tool_name: str, delay: float = 0.1) -> None:
    """Immediately check for logs from a newly started tool"""
    if not log_folder:
        return
        
    log_file = log_folder / f"{tool_name}.log"
    
    # Wait a bit for initial logs to be written
    for i in range(10):  # Check up to 10 times over 1 second
        await asyncio.sleep(delay)
        
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        lines = content.split('\n')
                        logs = []
                        for line in lines:
                            if line.strip():
                                logs.append({
                                    "source": tool_name,
                                    "content": line.strip(),
                                    "timestamp": time.time()
                                })
                        
                        if logs:
                            message = {
                                "type": "logs",
                                "data": logs
                            }
                            await broadcast_message(message)
                            
                            # Update position tracker
                            log_positions[str(log_file)] = log_file.stat().st_size
                            break
                            
            except Exception as e:
                logger.error(f"Error in immediate log check for {tool_name}: {e}")

async def broadcast_message(message: Dict[str, Any]) -> None:
    """Send message to all connected clients"""
    if not connected_clients:
        return

    disconnected = set()
    for client in connected_clients.copy():
        try:
            await client.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            disconnected.add(client)
        except Exception as e:
            logger.error(f"Error broadcasting to client: {e}")
            disconnected.add(client)

    for client in disconnected:
        connected_clients.discard(client)

async def send_tool_status(websocket: Optional[Any] = None) -> None:
    """Send current tool status to client(s)"""
    tools_status = await get_tool_status()
    
    message = {
        "type": "tool_status",
        "data": tools_status
    }
    
    if websocket:
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            pass
    else:
        await broadcast_message(message)

async def handle_websocket_message(websocket: Any, data: Dict[str, Any]) -> None:
    """Handle incoming WebSocket messages"""
    action = data.get('action')
    tool_name = data.get('tool_name')
    tool_type = data.get('tool_type')
    port_raw = data.get('port')
    
    # Convert port to int safely
    port = 0
    if port_raw is not None:
        try:
            port = int(port_raw)
        except (ValueError, TypeError):
            port = 0
    
    response: Dict[str, Any] = {"type": "response", "success": False, "message": "Unknown action"}
    
    try:
        if action == "start_tool":
            success = await start_tool(str(tool_name), str(tool_type), int(port))
            response = {
                "type": "response",
                "success": success,
                "message": f"{'Started' if success else 'Failed to start'} {tool_name}"
            }
                
        elif action == "stop_tool":
            success = await stop_tool(str(tool_name))
            response = {
                "type": "response",
                "success": success,
                "message": f"{'Stopped' if success else 'Failed to stop'} {tool_name}"
            }
        
        elif action == "reload_config":
            success = await reload_config()
            response = {
                "type": "response",
                "success": success,
                "message": f"{'Configuration reloaded successfully' if success else 'Failed to reload configuration'}"
            }
            if success:
                # Force a status update to show any new tools
                await send_tool_status()
                
        elif action == "relaunch_all":
            success = await relaunch_all_tools()
            response = {
                "type": "response",
                "success": success,
                "message": f"{'All tools relaunched successfully' if success else 'Failed to relaunch tools'}"
            }
                
        elif action == "get_logs":
            logs = await get_recent_logs()
            response = {
                "type": "logs",
                "data": logs
            }
            
        elif action == "get_status":
            await send_tool_status(websocket)
            return
        
        await websocket.send(json.dumps(response))
        
    except Exception as e:
        logger.error(f"Error handling action {action}: {e}")
        error_response = {
            "type": "response",
            "success": False,
            "message": f"Error processing {action}: {str(e)}"
        }
        await websocket.send(json.dumps(error_response))

async def monitor_log_files() -> None:
    """Enhanced log file monitoring with better error handling"""
    
    while True:
        try:
            if not log_folder or not connected_clients:
                await asyncio.sleep(0.5)
                continue
                
            for log_file in log_folder.glob("*.log"):
                # Skip monitoring the web server's own log file to prevent feedback loop
                if log_file.stem == "web_server":
                    continue
                    
                file_path = str(log_file)
                
                try:
                    current_size = log_file.stat().st_size
                    last_position = log_positions.get(file_path, 0)
                    
                    if current_size > last_position:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            f.seek(last_position)
                            new_content = f.read()
                            
                            if new_content.strip():
                                lines = new_content.strip().split('\n')
                                logs = []
                                for line in lines:
                                    if line.strip():
                                        logs.append({
                                            "source": log_file.stem,
                                            "content": line.strip(),
                                            "timestamp": time.time()
                                        })
                                
                                if logs:
                                    message = {
                                        "type": "logs", 
                                        "data": logs
                                    }
                                    await broadcast_message(message)
                                
                            log_positions[file_path] = current_size
                            
                    elif current_size < last_position:
                        # File was truncated or recreated, reset position
                        log_positions[file_path] = 0
                        
                except FileNotFoundError:
                    # Log file was deleted, remove from tracking
                    if file_path in log_positions:
                        del log_positions[file_path]
                except Exception as e:
                    logger.error(f"Error monitoring log file {log_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in log monitoring: {e}")
            
        await asyncio.sleep(0.2)

async def websocket_handler(websocket: Any) -> None:
    """Handle WebSocket connections"""
    connected_clients.add(websocket)
    logger.info(f"Client connected. Total: {len(connected_clients)}")
    
    try:
        await send_tool_status(websocket)
        
        # Send initial logs with different message type
        logs = await get_recent_logs(50)
        if logs:
            initial_message = {
                "type": "initial_logs",  # Use different type for initial logs
                "data": logs
            }
            await websocket.send(json.dumps(initial_message))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                await handle_websocket_message(websocket, data)
            except json.JSONDecodeError:
                error_response = {
                    "type": "response",
                    "success": False,
                    "message": "Invalid JSON message"
                }
                await websocket.send(json.dumps(error_response))
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connected_clients.discard(websocket)

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler to serve static files"""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        if args[1] != "200":
            super().log_message(format, *args)
    
    def end_headers(self) -> None:
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self) -> None:
        if self.path == '/' or self.path == '/index.html':
            html_file = ROOT_DIR / 'index.html'
            
            if html_file.exists():
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                with open(html_file, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                error_html = f'''
                <!DOCTYPE html>
                <html>
                <body>
                    <h1>404 - index.html not found</h1>
                    <p>Make sure index.html is in the project root directory.</p>
                    <p>Current directory: {ROOT_DIR}</p>
                </body>
                </html>
                '''
                self.wfile.write(error_html.encode('utf-8'))
                return
        
        if self.path.startswith('/images/'):
            image_name = self.path[8:]

            images_path = ROOT_DIR / 'tool_images' / image_name
            
            if images_path.exists():
                self.send_response(200)
                
                if image_name.lower().endswith('.png'):
                    self.send_header('Content-type', 'image/png')
                elif image_name.lower().endswith(('.jpg', '.jpeg')):
                    self.send_header('Content-type', 'image/jpeg')
                elif image_name.lower().endswith('.gif'):
                    self.send_header('Content-type', 'image/gif')
                elif image_name.lower().endswith('.svg'):
                    self.send_header('Content-type', 'image/svg+xml')
                else:
                    self.send_header('Content-type', 'image/png')
                
                self.end_headers()
                with open(images_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
            
            logger.warning(f"Image not found: {image_name}")
            self.send_response(404)
            self.end_headers()
            return
        
        super().do_GET()

def run_http_server(port: int = 8080) -> None:
    """Run HTTP server in a separate thread"""
    server = HTTPServer(('localhost', port), CustomHTTPRequestHandler)
    logger.info(f"HTTP server running on http://localhost:{port}")
    server.serve_forever()

def cleanup_processes() -> None:
    """Cleanup all processes"""
    logger.info("Cleaning up processes...")
    for tool_name in list(server_processes.keys()):
        kill_process_by_name(tool_name)

async def main() -> None:
    """Main function"""
    global config, log_folder, last_tool_status
    
    try:
        # Setup logging first
        log_folder = setup_logging()
        
        # Check for updates
        update_available, current_version, latest_version = check_for_updates()
        
        # Display startup message
        display_startup_message(log_folder, update_available, current_version, latest_version)
        
        # Initialize config
        config = Config()
        config.load_workcell_config()
        
        # Initialize last_tool_status
        initial_status = await get_tool_status()
        last_tool_status = {tool['name']: tool['status'] for tool in initial_status}
        
        # Start HTTP server in background thread
        http_port = 8080
        http_thread = threading.Thread(target=run_http_server, args=(http_port,), daemon=True)
        http_thread.start()
        
        logger.info("Starting WebSocket server on ws://localhost:8765")
        
        # Start WebSocket server
        server = await websockets.serve(websocket_handler, "localhost", 8765)
        logger.info("WebSocket server ready on ws://localhost:8765")
        logger.info("HTTP server running on http://localhost:8080")
        
        # Start monitoring tasks
        asyncio.create_task(monitor_log_files())
        asyncio.create_task(monitor_tool_processes())
        
        browser_url = f"http://localhost:{http_port}"
        logger.info(f"You can also access the web interface at {browser_url}")
        open_browser(browser_url, delay=2.0)
        # Wait for server to close
        await server.wait_closed()
            
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return
    finally:
        cleanup_processes()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("\n🛑 Galago Web Server stopped by user")
        print("=" * 80)