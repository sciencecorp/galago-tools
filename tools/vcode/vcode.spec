# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for VCode Labeler Driver

BUILD REQUIREMENTS:
- Python 3.9 (32-bit) - REQUIRED for DLL compatibility
- Windows only
- Create venv with 32-bit Python
- Install: pip install pyinstaller grpcio grpcio-reflection protobuf pythonnet pydantic

BUILD COMMAND:
    pyinstaller vcode.spec --clean --noconfirm
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
    # .NET interop
    'clr',
    'pythonnet',
    'pydantic',
    # Local modules
    'tools',
    'tools.vcode',
    'tools.vcode.server',
    'tools.vcode.driver',
    'tools.base_server',
    'tools.grpc_interfaces',
]

# Include the VCode DLLs
deps_dir = os.path.join(spec_dir, 'deps')
binaries = []
if os.path.exists(deps_dir):
    for dll_file in os.listdir(deps_dir):
        if dll_file.endswith('.dll'):
            binaries.append((os.path.join(deps_dir, dll_file), 'deps'))

a = Analysis(
    ['entry_point.py'],
    pathex=[project_root],
    binaries=binaries,
    datas=[
        (os.path.join(project_root, 'tools', 'grpc_interfaces'), 'tools/grpc_interfaces'),
        (os.path.join(spec_dir, 'deps'), 'tools/vcode/deps'),
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
    name='vcode',
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
    name='vcode',
)

