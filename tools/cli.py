import os
import sys
import argparse
import logging
import subprocess
from tools import __version__ as galago_version

# Move heavy imports inside functions to delay loading
def get_shell_command(tool: str, file: str) -> list[str]:
    if tool:
        return [sys.executable, '-m', f'tools.{tool}.server']
    elif file:
        return [sys.executable, file]
    else:
        raise RuntimeError("Either tool or file must be provided.")

def serve() -> None:
    """Legacy serve function for backwards compatibility"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True, help="Port must be provided.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--tool', help="Name of the tool to run (e.g., 'xpeel').")
    group.add_argument('--file', help="Path to the file to run.")
    known, remaining = parser.parse_known_args()
    
    use_shell = os.name == 'nt'
    sys.argv = [sys.argv[0]] + remaining
    command = get_shell_command(str(known.tool).lower(), known.file)
    command.append(f'--port={known.port}')
    
    # Set the PYTHONPATH to include the project root.
    env = os.environ.copy()
    project_root = os.getcwd()
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = project_root + (os.pathsep + current_pythonpath if current_pythonpath else "")
    
    subprocess.Popen(command, shell=use_shell, universal_newlines=True, env=env)

def start_web_server() -> bool:
    """Start the web socket server in a separate process"""
    try:
        # Import here to avoid import issues
        from tools.web_server import main as web_server_main
        import asyncio
        
        # Run the web server in the current process
        asyncio.run(web_server_main())
    except Exception as e:
        print(f"Failed to start web server: {e}")
        return False
    return True

def launch_web_only() -> int:
    """Launch only the web server without desktop app"""
    try:
        import asyncio
        from tools.web_server import main as web_server_main
        asyncio.run(web_server_main())
        return 0
    except Exception as e:
        print(f"Failed to start web server: {e}")
        return 1

def main() -> None:
    """Main entry point for Galago Tools Manager CLI"""
    
    # Define top-level arguments
    parser = argparse.ArgumentParser(
        description="Galago Tools Manager - Modern Lab Automation Interface",
        add_help=False
    )
    parser.add_argument("--help", action="help", help="Show this help message and exit")
    parser.add_argument("--version", action="version", version=f"Galago Tools Manager {galago_version}", help="Show program version and exit")
    parser.add_argument("--discover", action="store_true", help="Autodiscover tools")
    parser.add_argument("--console", action="store_true", help="Launch in headless mode. No GUI.")
    parser.add_argument("--web-only", action="store_true", help="Launch web server only (no desktop app)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--legacy", action="store_true", help="Launch legacy app.")
    parser.add_argument("--list", action="store_true", help="List available tools")
    parser.add_argument("--info", metavar="TOOL", help="Get information about a specific tool")
    
    # Parse known arguments and get the remaining arguments (if any)
    known, remaining = parser.parse_known_args()
    
    # Set up logging
    level = logging.DEBUG if known.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Remove the consumed arguments from sys.argv
    sys.argv = [sys.argv[0]] + remaining
    
    # Handle legacy modes
    if known.console:
        from tools.launch_console import main as launch_console_main
        sys.exit(launch_console_main())
    elif known.legacy:
        from tools.launch_tools import main as launch_tools_main
        sys.exit(launch_tools_main())
    elif known.discover:
        from tools.discover_tools import main as autodiscover_main
        sys.exit(autodiscover_main())
    elif known.web_only:
        # Launch web server only
        sys.exit(launch_web_only())
    elif known.list:
        from tools.utils import list_available_tools
        tools = list_available_tools()
        print("Available tools:")
        for tool in tools:
            print(f"- {tool}")
        sys.exit(0)
    elif known.info:
        from tools.utils import print_tool_server_info
        print_tool_server_info(str(known.info).lower())
        sys.exit(0)
    else:
        # Default: Lanch tools manager web server
        try:
            from tools.web_server import main as web_server_main
            import asyncio
            asyncio.run(web_server_main())
        except KeyboardInterrupt:
            print("Shutting down...")
            sys.exit(0)
        except Exception as e:
            logging.error(f"Failed to start Galago Tools Manager: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()