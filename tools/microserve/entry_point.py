#!/usr/bin/env python3
"""
MicroServe Driver Entry Point

This script serves as the main entry point for the MicroServe plate hotel gRPC server
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
    """Main entry point for the MicroServe driver."""
    # Required for Windows executables
    freeze_support()
    setup_paths()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    
    # Import server implementation
    from tools.microserve.server import MicroserveServer
    from tools.base_server import serve
    
    # Get port from environment (controlled by Electron) or default
    port = os.environ.get("GRPC_PORT", "50051")
    
    logging.info(f"MicroServe driver starting on port {port}")
    serve(MicroserveServer(), port)


if __name__ == "__main__":
    main()

