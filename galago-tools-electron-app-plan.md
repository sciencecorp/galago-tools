# Galago Tools Migration Guide

This document outlines the changes needed in the **galago-tools** repository to support the Electron desktop application.

## Overview

The galago-tools repository contains the gRPC server implementations for each lab tool (PF400, Hamilton, Opentrons, etc.). For the Electron desktop app, these need to be:

1. Compiled into standalone executables using PyInstaller
2. Built with 32-bit Python (for hardware driver compatibility)
3. Configured to accept dynamic port assignment

## Required Changes

### 1. Create Entry Points for Each Tool

Each tool driver needs a `entry_point.py` that can be compiled by PyInstaller.

**Template: `tools/<tool_name>/entry_point.py`**

```python
#!/usr/bin/env python3
"""
<Tool Name> Driver Entry Point

This script serves as the main entry point for the <Tool Name> gRPC server
when packaged as a standalone executable using PyInstaller.
"""

import os
import sys
from multiprocessing import freeze_support
from concurrent import futures
import grpc

def setup_paths():
    """Setup Python paths for bundled executable."""
    if getattr(sys, 'frozen', False):
        bundle_dir = os.path.dirname(sys.executable)
        if bundle_dir not in sys.path:
            sys.path.insert(0, bundle_dir)

def main():
    # Required for Windows executables
    freeze_support()
    setup_paths()
    
    # Import gRPC service implementation
    from <tool_name>.server import <ToolName>Servicer
    from grpc_interfaces import <tool_name>_pb2_grpc
    
    # Get port from environment (controlled by Electron)
    port = int(os.environ.get("GRPC_PORT", 50051))
    
    # Create gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    <tool_name>_pb2_grpc.add_<ToolName>Servicer_to_server(
        <ToolName>Servicer(), 
        server
    )
    
    server.add_insecure_port(f'127.0.0.1:{port}')
    
    print(f"<Tool Name> driver starting on port {port}")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    main()
```

### 2. Create PyInstaller Spec Files

**IMPORTANT**: Many lab instruments require 32-bit drivers. You MUST build these with 32-bit Python.

**Template: `tools/<tool_name>/<tool_name>.spec`**

```python
# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for <Tool Name> Driver

BUILD REQUIREMENTS:
- Python 3.9 (32-bit) from python.org
- Create venv with 32-bit Python
- Install: pip install pyinstaller grpcio protobuf <tool-specific-deps>

BUILD COMMAND:
    pyinstaller <tool_name>.spec --clean --noconfirm
"""

block_cipher = None

# Tool-specific hidden imports
hiddenimports = [
    'grpc',
    'grpc._cython',
    'google.protobuf',
    'concurrent.futures',
    # Add tool-specific imports here:
    # 'serial',  # For serial communication
    # 'pywin32',  # For Windows COM
    # etc.
]

a = Analysis(
    ['entry_point.py'],
    pathex=['.', '..'],
    binaries=[
        # Include any DLLs required by the tool
        # ('path/to/driver.dll', '.'),
    ],
    datas=[
        # Include config files
        # ('config/*.json', 'config'),
    ],
    hiddenimports=hiddenimports,
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas'],
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='<tool_name>',
    debug=False,
    console=True,  # Keep True for debugging
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='<tool_name>',
)
```

### 3. Add Common Dependencies

**Update `requirements.txt`** (or create tool-specific ones):

```
grpcio>=1.50.0
protobuf>=4.0.0
pyinstaller>=6.0.0
# Tool-specific dependencies
pyserial>=3.5  # If using serial ports
pywin32>=305  # If using Windows COM (Windows only)
```

### 4. Build Scripts

**`scripts/build_tools.ps1`** (Windows - for 32-bit builds):

```powershell
# Build all tool drivers with 32-bit Python
# Requires Python 3.9 32-bit installed

$ErrorActionPreference = "Stop"

# Path to 32-bit Python (adjust as needed)
$Python32 = "C:\Python39-32\python.exe"

$Tools = @("pf400", "hamilton", "opentrons2", "liconic", "bravo", "cytation")

foreach ($tool in $Tools) {
    Write-Host "Building $tool..." -ForegroundColor Yellow
    
    Set-Location "tools\$tool"
    
    # Create venv with 32-bit Python
    & $Python32 -m venv venv32
    .\venv32\Scripts\activate
    
    # Install dependencies
    pip install -r requirements.txt
    pip install pyinstaller
    
    # Build
    pyinstaller "$tool.spec" --clean --noconfirm
    
    deactivate
    Set-Location ..\..
    
    Write-Host "$tool built successfully!" -ForegroundColor Green
}

# Copy all binaries to output
New-Item -ItemType Directory -Path "dist\tools" -Force
foreach ($tool in $Tools) {
    Copy-Item -Path "tools\$tool\dist\$tool" -Destination "dist\tools\" -Recurse
}

Write-Host "All tools built! Output in dist\tools\" -ForegroundColor Green
```

### 5. Update Directory Structure

Your galago-tools repo should look like:

```
galago-tools/
├── tools/
│   ├── pf400/
│   │   ├── entry_point.py       # NEW: Entry point for PyInstaller
│   │   ├── pf400.spec           # NEW: PyInstaller spec
│   │   ├── requirements.txt     # Tool-specific dependencies
│   │   ├── server.py            # Existing: gRPC server implementation
│   │   └── driver/              # Existing: Hardware driver code
│   ├── hamilton/
│   │   ├── entry_point.py
│   │   ├── hamilton.spec
│   │   └── ...
│   └── ... (other tools)
├── grpc_interfaces/             # Generated protobuf files
├── scripts/
│   └── build_tools.ps1          # NEW: Build script
├── requirements.txt
└── README.md
```

## Build Process for Desktop

1. **Install 32-bit Python 3.9** from python.org (Windows x86 installer)

2. **For each tool**:
   ```bash
   cd tools/<tool_name>
   C:\Python39-32\python.exe -m venv venv32
   venv32\Scripts\activate
   pip install -r requirements.txt
   pip install pyinstaller
   pyinstaller <tool_name>.spec --clean
   ```

3. **Copy binaries to galago-desktop**:
   ```bash
   cp -r dist/<tool_name> ../galago-core/galago-desktop/resources/binaries/tools/
   ```

## Integration with Electron

The Electron app can manage tool drivers in two modes:

### Mode 1: Managed (Electron starts tools)

Copy binaries to `galago-desktop/resources/binaries/tools/` and configure in `tools-config.json`:

```json
{
  "tools": [
    {
      "name": "pf400",
      "binaryName": "pf400",
      "port": 50051,
      "managed": true,
      "is32bit": true
    }
  ]
}
```

### Mode 2: External (Tools run independently)

Tools can still run as separate services (useful for debugging or shared tools):

```json
{
  "tools": [
    {
      "name": "pf400",
      "port": 50051,
      "managed": false
    }
  ]
}
```

## Testing

Before packaging:

1. Run the tool driver standalone:
   ```bash
   cd tools/pf400
   python entry_point.py
   ```

2. Test gRPC connection:
   ```python
   import grpc
   from grpc_interfaces import pf400_pb2_grpc
   
   channel = grpc.insecure_channel('localhost:50051')
   stub = pf400_pb2_grpc.PF400Stub(channel)
   response = stub.GetStatus(pf400_pb2.Empty())
   print(response)
   ```

3. Test the compiled binary:
   ```bash
   cd tools/pf400/dist/pf400
   ./pf400.exe  # or ./pf400 on Unix
   ```

## Troubleshooting

### "DLL not found" errors
Include the required DLLs in the spec file's `binaries` section.

### 32-bit vs 64-bit
Many lab instruments only have 32-bit drivers. Always build with 32-bit Python on Windows.

### Port conflicts
The Electron app automatically finds available ports. Each tool should accept `GRPC_PORT` environment variable.

### Serial port access
Ensure the user running the app has permissions to access serial ports (COM ports on Windows, /dev/tty* on Unix).

