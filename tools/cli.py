import sys
import argparse
import logging
from tools.launch_tools import main as launch_tools_main
from tools.launch_console import main as launch_console_main

def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--console", action="store_true", help="Launch in console mode")
    known, remaining = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + remaining
    
    if known.console:
        sys.exit(launch_console_main())
    else:
        sys.exit(launch_tools_main())
