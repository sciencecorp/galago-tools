#!/usr/bin/env python3
"""
ALPS 3000 Driver Entry Point

This script serves as the main entry point for the ALPS 3000 gRPC server
when packaged as a standalone executable using PyInstaller.
"""

import os
import sys
import logging
from multiprocessing import freeze_support


def setup_paths() -> None:
    """Setup Python paths for bundled executable."""
    if getattr(sys, 'frozen', False):
        bundle_dir = os.path.dirname(sys.executable)
        if bundle_dir not in sys.path:
            sys.path.insert(0, bundle_dir)


def main() -> None:
    """Main entry point for the ALPS 3000 driver."""
    # Required for Windows executables
    freeze_support()
    setup_paths()
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    
    # Import server implementation
    from tools.alps3000.server import ALPS3000Server
    from tools.base_server import serve
    
    # Get port from environment (controlled by Electron) or default
    port = os.environ.get("GRPC_PORT", "50051")
    
    logging.info(f"ALPS 3000 driver starting on port {port}")
    serve(ALPS3000Server(), port)


if __name__ == "__main__":
    main()

