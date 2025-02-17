import sys
from tools.launch_tools import main as launch_tools_main
from tools.launch_console import main as launch_console_main

def launch_all_servers() -> None:
    sys.exit(launch_tools_main())

def launch_console() -> None:
    sys.exit(launch_console_main())