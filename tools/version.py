"""
Galago Tools version information.
This file is auto-updated by the bump script.
"""

# Version information
__version__ = '0.16.3'  # Update this version string as needed

# Parse version components for easier access
VERSION_PARTS = __version__.split('.')
VERSION_MAJOR = int(VERSION_PARTS[0])
VERSION_MINOR = int(VERSION_PARTS[1])
VERSION_PATCH = int(VERSION_PARTS[2]) if len(VERSION_PARTS) > 2 else 0

# String representations
VERSION_SHORT = f"{VERSION_MAJOR}.{VERSION_MINOR}"
VERSION_FULL = __version__