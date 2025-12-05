#!/usr/bin/env python3
"""
Bravo Driver Entry Point

This script serves as the main entry point for the Bravo gRPC server
when packaged as a standalone executable using PyInstaller.

NOTE: This driver requires Windows and uses COM automation.
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
    """Main entry point for the Bravo driver."""
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
    from tools.bravo.server import BravoServer
    from tools.base_server import serve
    
    # Get port from environment (controlled by Electron) or default
    port = os.environ.get("GRPC_PORT", "50051")
    
    logging.info(f"Bravo driver starting on port {port}")
    serve(BravoServer(), port)


if __name__ == "__main__":
    main()

