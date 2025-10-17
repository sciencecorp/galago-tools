#!/usr/bin/env python3

import asyncio
import websockets
import json
import logging
import os
import sys
import subprocess
import socket
import signal as os_signal
import time
from pathlib import Path
from typing import Dict, Set, Optional
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Add the project root to Python path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

try:
    from tools.app_config import Config
    from tools.utils import get_shell_command
except ImportError as e:
    logging.error(f"Failed to import tools modules: {e}")
    logging.error("Make sure the 'tools' directory is in the project root with app_config.py and utils.py")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# Global state
connected_clients: Set = set()
server_processes: Dict[str, subprocess.Popen] = {}
config: Optional[Config] = None
log_folder: Optional[Path] = None
log_positions: Dict[str, int] = {}

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

def kill_by_process_id(process_id: int):
    """Kill a process by PID"""
    try:
        if os.name == 'nt':
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(process_id)])
        else:
            os.kill(process_id, os_signal.SIGTERM)
            time.sleep(0.5)
            try:
                os.kill(process_id, os_signal.SIGKILL)
            except ProcessLookupError:
                pass
    except Exception as e:
        logger.error(f"Failed to kill process {process_id}: {e}")

def kill_process_by_name(process_name: str):
    """Kill a process by name"""
    if process_name not in server_processes:
        return
    try:
        process = server_processes[process_name]
        kill_by_process_id(process.pid)
        del server_processes[process_name]
    except Exception as e:
        logger.warning(f"Failed to kill process {process_name}: {e}")

async def get_tool_status():
    """Get current status of all tools"""
    tools_status = []
    
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

async def start_tool(tool_name: str, tool_type: str, port: int):
    """Start a tool process"""
    try:
        kill_process_by_name(tool_name)
        
        if is_port_occupied(port):
            raise Exception(f"Port {port} is already occupied")
        
        cmd = get_shell_command(tool_type=tool_type, port=port)
        os.chdir(ROOT_DIR)
        
        if log_folder:
            log_file = log_folder / f"{tool_name}.log"
            with open(log_file, 'w') as f:
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    shell=os.name == 'nt'
                )
        else:
            process = subprocess.Popen(
                cmd,
                universal_newlines=True,
                shell=os.name == 'nt'
            )
        
        server_processes[tool_name] = process
        logger.info(f"Started {tool_name} on port {port}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to start {tool_name}: {e}")
        return False

async def stop_tool(tool_name: str):
    """Stop a tool process"""
    try:
        kill_process_by_name(tool_name)
        logger.info(f"Stopped {tool_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to stop {tool_name}: {e}")
        return False

async def get_recent_logs(lines: int = 100) -> list:
    """Get recent logs from all log files"""
    logs = []
    
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

async def broadcast_message(message: dict):
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

async def send_tool_status(websocket=None):
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

async def handle_websocket_message(websocket, data):
    """Handle incoming WebSocket messages"""
    action = data.get('action')
    tool_name = data.get('tool_name')
    tool_type = data.get('tool_type')
    port = data.get('port')
    
    response = {"type": "response", "success": False, "message": "Unknown action"}
    
    try:
        if action == "start_tool":
            success = await start_tool(tool_name, tool_type, port)
            response = {
                "type": "response",
                "success": success,
                "message": f"{'Started' if success else 'Failed to start'} {tool_name}"
            }
            if success:
                await send_tool_status()
                
        elif action == "stop_tool":
            success = await stop_tool(tool_name)
            response = {
                "type": "response",
                "success": success,
                "message": f"{'Stopped' if success else 'Failed to stop'} {tool_name}"
            }
            if success:
                await send_tool_status()
                
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

async def monitor_log_files():
    """Monitor log files for new content and broadcast updates - async version"""
    logger.info("Starting real-time log monitoring task")
    
    while True:
        try:
            if not log_folder or not connected_clients:
                await asyncio.sleep(1)
                continue
                
            for log_file in log_folder.glob("*.log"):
                file_path = str(log_file)
                
                try:
                    current_size = log_file.stat().st_size
                    last_position = log_positions.get(file_path, 0)
                    
                    if current_size > last_position:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            f.seek(last_position)
                            new_lines = f.readlines()
                            
                            if new_lines:
                                logs = []
                                for line in new_lines:
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
                                    logger.debug(f"Broadcasted {len(logs)} new log entries from {log_file.stem}")
                                
                            log_positions[file_path] = current_size
                            
                except Exception as e:
                    logger.error(f"Error monitoring log file {log_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in log monitoring: {e}")
            
        await asyncio.sleep(0.5)

async def websocket_handler(websocket):
    """Handle WebSocket connections"""
    connected_clients.add(websocket)
    logger.info(f"Client connected. Total: {len(connected_clients)}")
    
    try:
        await send_tool_status(websocket)
        
        # Send initial logs with different message type
        logs = await get_recent_logs(50)
        if logs:
            message = {
                "type": "initial_logs",  # Use different type for initial logs
                "data": logs
            }
            await websocket.send(json.dumps(message))
        
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
        logger.info(f"Client disconnected. Total: {len(connected_clients)}")

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler to serve static files"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)
    
    def log_message(self, format, *args):
        if args[1] != "200":
            super().log_message(format, *args)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            html_file = ROOT_DIR / 'web_interface.html'
            
            if html_file.exists():
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                with open(html_file, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
                return
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                error_html = f'''
                <!DOCTYPE html>
                <html>
                <body>
                    <h1>404 - web_interface.html not found</h1>
                    <p>Make sure web_interface.html is in the project root directory.</p>
                    <p>Current directory: {ROOT_DIR}</p>
                </body>
                </html>
                '''
                self.wfile.write(error_html.encode('utf-8'))
                return
        
        if self.path.startswith('/images/'):
            image_name = self.path[8:]
            
            possible_paths = [
                ROOT_DIR / 'src' / 'tool_images' / image_name,
                ROOT_DIR / 'images' / image_name,
                ROOT_DIR / 'tool_images' / image_name,
                ROOT_DIR / image_name
            ]
            
            for image_path in possible_paths:
                if image_path.exists():
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
                    with open(image_path, 'rb') as f:
                        self.wfile.write(f.read())
                    return
            
            logger.warning(f"Image not found: {image_name}")
            self.send_response(404)
            self.end_headers()
            return
        
        super().do_GET()

def run_http_server(port: int = 8080):
    """Run HTTP server in a separate thread"""
    server = HTTPServer(('localhost', port), CustomHTTPRequestHandler)
    logger.info(f"HTTP server running on http://localhost:{port}")
    server.serve_forever()

def cleanup_processes():
    """Cleanup all processes"""
    logger.info("Cleaning up processes...")
    for tool_name in list(server_processes.keys()):
        kill_process_by_name(tool_name)

async def main():
    """Main function"""
    global config, log_folder
    
    try:
        config = Config()
        config.load_workcell_config()
        
        log_folder = ROOT_DIR / "data" / "trace_logs" / str(int(time.time()))
        log_folder.mkdir(parents=True, exist_ok=True)
        
        # Start HTTP server in background thread
        http_thread = threading.Thread(target=run_http_server, daemon=True)
        http_thread.start()
        
        logger.info("Starting WebSocket server on ws://localhost:8765")
        
        # Start WebSocket server
        server = await websockets.serve(websocket_handler, "localhost", 8765)
        logger.info("WebSocket server ready on ws://localhost:8765")
        logger.info("HTTP server running on http://localhost:8080")
        
        # Start log monitoring as an async task (not a thread)
        log_task = asyncio.create_task(monitor_log_files())
        logger.info("Real-time log streaming enabled")
        
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