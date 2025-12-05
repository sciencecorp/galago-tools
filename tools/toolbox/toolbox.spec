# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for ToolBox Utility Service

BUILD REQUIREMENTS:
- Python 3.9
- Create venv with appropriate Python version
- Install: pip install pyinstaller grpcio grpcio-reflection protobuf pydantic

BUILD COMMAND:
    pyinstaller toolbox.spec --clean --noconfirm
"""

import os
import sys

block_cipher = None

# Get the project root directory
spec_dir = os.path.dirname(os.path.abspath(SPEC))
project_root = os.path.abspath(os.path.join(spec_dir, '..', '..'))

# Tool-specific hidden imports
hiddenimports = [
    # gRPC dependencies
    'grpc',
    'grpc._cython',
    'grpc._cython.cygrpc',
    'grpc.experimental',
    'grpc_reflection',
    'grpc_reflection.v1alpha',
    'grpc_reflection.v1alpha.reflection',
    'google.protobuf',
    'google.protobuf.descriptor',
    'google.protobuf.descriptor_pool',
    'google.protobuf.message',
    'google.protobuf.reflection',
    'google.protobuf.symbol_database',
    'google.protobuf.json_format',
    'google.protobuf.struct_pb2',
    'concurrent.futures',
    # Tool-specific imports
    'pydantic',
    'subprocess',
    # Local modules
    'tools',
    'tools.toolbox',
    'tools.toolbox.server',
    'tools.toolbox.utils',
    'tools.toolbox.python_subprocess',
    'tools.base_server',
    'tools.grpc_interfaces',
    'tools.grpc_interfaces.tool_base_pb2',
    'tools.grpc_interfaces.tool_base_pb2_grpc',
    'tools.grpc_interfaces.tool_driver_pb2',
    'tools.grpc_interfaces.tool_driver_pb2_grpc',
    'tools.app_config',
    'appdirs',
    'serial',
    'serial.tools',
    'serial.tools.list_ports',
    'serial.tools.list_ports_posix',
    'serial.tools.list_ports_common',
]

a = Analysis(
    ['entry_point.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'tools', 'grpc_interfaces'), 'tools/grpc_interfaces'),
        (os.path.join(spec_dir, 'slack_templates'), 'tools/toolbox/slack_templates'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy', 'PIL'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='toolbox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='toolbox',
)

