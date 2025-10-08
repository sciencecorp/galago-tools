import os
import sys
import argparse
import logging
import subprocess

# Move heavy imports inside functions to delay loading
def get_shell_command(tool: str, file: str) -> list[str]:
    if tool:
        return [sys.executable, '-m', f'tools.{tool}.server']
    elif file:
        return [sys.executable, file]
    else:
        raise RuntimeError("Either tool or file must be provided.")

def serve() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True, help="Port must be provided.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--tool', help="Name of the tool to run (e.g., 'xpeel').")
    group.add_argument('--file', help="Path to the file to run.")
    
    known, remaining = parser.parse_known_args()
    use_shell = os.name == 'nt'
    sys.argv = [sys.argv[0]] + remaining
    command = get_shell_command(known.tool, known.file)
    command.append(f'--port={known.port}')
    
    # Set the PYTHONPATH to include the project root.
    env = os.environ.copy()
    project_root = os.getcwd()
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = project_root + (os.pathsep + current_pythonpath if current_pythonpath else "")
    
    subprocess.Popen(command, shell=use_shell, universal_newlines=True, env=env)

def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    
    # Define top-level arguments that you want to process
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--help", action="help", help="Show this help message and exit")
    parser.add_argument("--discover", action="store_true", help="Autodiscover tools")
    parser.add_argument("--console", action="store_true", help="Launch in console mode")
    
    # Parse known arguments and get the remaining arguments (if any)
    known, remaining = parser.parse_known_args()
    
    # Remove the consumed arguments from sys.argv
    sys.argv = [sys.argv[0]] + remaining
    
    if known.console:
        from tools.launch_console import main as launch_console_main
        sys.exit(launch_console_main())
    elif known.discover:
        from tools.discover_tools import main as autodiscover_main
        sys.exit(autodiscover_main())
    else:
        from tools.launch_tools import main as launch_tools_main
        sys.exit(launch_tools_main())

if __name__ == "__main__":
    main()