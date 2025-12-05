#!/usr/bin/env python3
"""
Build a single tool driver for Electron Desktop App.

This script is useful for building individual tools during development
or for CI/CD pipelines.

Usage:
    python scripts/build_single_tool.py pf400
    python scripts/build_single_tool.py --all
    python scripts/build_single_tool.py pf400 bravo --clean
"""

import argparse
import os
import subprocess
import sys
import shutil
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# All available tools
ALL_TOOLS = [
    "alps3000",
    "bioshake",
    "bravo",
    "cytation",
    "dataman70",
    "hamilton",
    "hig_centrifuge",
    "liconic",
    "microserve",
    "opentrons2",
    "pf400",
    "plateloc",
    "plr",
    "pyhamilton",
    "spectramax",
    "toolbox",
    "vcode",
    "vprep",
    "xpeel",
]


def generate_grpc_interfaces() -> bool:
    """Generate gRPC interface files from proto definitions."""
    print("Generating gRPC interfaces...")
    try:
        # Run the setup.py build_py to generate interfaces
        result = subprocess.run(
            [sys.executable, "setup.py", "build_py", "--build-lib", "."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Warning: {result.stderr}")
        return True
    except Exception as e:
        print(f"Warning: Could not generate gRPC interfaces: {e}")
        return False


def build_tool(tool_name: str, clean: bool = False, output_dir: Path | None = None) -> bool:
    """Build a single tool driver."""
    tool_dir = PROJECT_ROOT / "tools" / tool_name
    spec_file = tool_dir / f"{tool_name}.spec"
    
    if not spec_file.exists():
        print(f"Error: Spec file not found: {spec_file}")
        return False
    
    print(f"\nBuilding {tool_name}...")
    print("-" * 40)
    
    # Clean if requested
    if clean:
        build_dir = tool_dir / "build"
        dist_dir = tool_dir / "dist"
        if build_dir.exists():
            shutil.rmtree(build_dir)
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
    
    # Run PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        str(spec_file),
        "--clean",
        "--noconfirm",
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=tool_dir,
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            print(f"PyInstaller failed:\n{result.stderr}")
            return False
        
        # Verify output exists
        built_dir = tool_dir / "dist" / tool_name
        if not built_dir.exists():
            print(f"Error: Build output not found at {built_dir}")
            return False
        
        # Copy to output directory if specified
        if output_dir:
            dest_dir = output_dir / tool_name
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.copytree(built_dir, dest_dir)
            print(f"SUCCESS: Built to {dest_dir}")
        else:
            print(f"SUCCESS: Built to {built_dir}")
        
        return True
        
    except Exception as e:
        print(f"Error building {tool_name}: {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build tool drivers for Electron Desktop App"
    )
    parser.add_argument(
        "tools",
        nargs="*",
        help="Tool names to build (or use --all for all tools)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Build all available tools",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build directories before building",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "dist" / "tools",
        help="Output directory for built tools",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available tools and exit",
    )
    parser.add_argument(
        "--skip-grpc",
        action="store_true",
        help="Skip gRPC interface generation",
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("Available tools:")
        for tool in ALL_TOOLS:
            print(f"  - {tool}")
        return 0
    
    # Determine which tools to build
    if args.all:
        tools = ALL_TOOLS
    elif args.tools:
        tools = args.tools
        # Validate tool names
        for tool in tools:
            if tool not in ALL_TOOLS:
                print(f"Error: Unknown tool '{tool}'")
                print(f"Available tools: {', '.join(ALL_TOOLS)}")
                return 1
    else:
        parser.print_help()
        return 1
    
    print("=" * 44)
    print("Galago Tools Builder for Electron Desktop")
    print("=" * 44)
    print(f"Python: {sys.executable}")
    print(f"Tools to build: {', '.join(tools)}")
    print()
    
    # Generate gRPC interfaces
    if not args.skip_grpc:
        generate_grpc_interfaces()
    
    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)
    
    # Build each tool
    results = {}
    for tool in tools:
        success = build_tool(tool, clean=args.clean, output_dir=args.output)
        results[tool] = "SUCCESS" if success else "FAILED"
    
    # Summary
    print()
    print("=" * 44)
    print("Build Summary")
    print("=" * 44)
    
    success_count = sum(1 for r in results.values() if r == "SUCCESS")
    failed_count = sum(1 for r in results.values() if r == "FAILED")
    
    for tool, status in sorted(results.items()):
        color = "\033[92m" if status == "SUCCESS" else "\033[91m"
        reset = "\033[0m"
        print(f"  {color}{tool}: {status}{reset}")
    
    print()
    print(f"Total: {success_count} succeeded, {failed_count} failed")
    print(f"Output directory: {args.output}")
    
    return 1 if failed_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

