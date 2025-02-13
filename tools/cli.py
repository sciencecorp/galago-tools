import sys
import argparse
import logging
from tools.launch_tools import main as launch_tools_main
from tools.launch_console import main as launch_console_main
from tools.discover_tools import main as autodiscover_main
def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    # Define top-level arguments that you want to process
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--help", action="help", help="Show this help message and exit")
    parser.add_argument("--discover", action="store_true", help="Autodiscover tools")
    parser.add_argument("--console", action="store_true", help="Launch in console mode")
    parser.add_argument("--port", help="Port for tool servers")
    
    # Parse known arguments and get the remaining arguments (if any)
    known, remaining = parser.parse_known_args()
    
    # Remove the consumed arguments from sys.argv
    sys.argv = [sys.argv[0]] + remaining

    if known.console:
        sys.exit(launch_console_main())
    elif known.discover:
        sys.exit(autodiscover_main())
    else:
        sys.exit(launch_tools_main())
