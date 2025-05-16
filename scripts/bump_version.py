#!/usr/bin/env python
"""
Usage: python bump_version.py [major|minor|patch]
Bumps the version in tools/version.py according to server rules.
"""
import re
import sys
import os

# Path to version.py
VERSION_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    'tools', 
    'version.py'
)

def get_version():
    # Read version.py
    with open(VERSION_PATH, 'r') as f:
        content = f.read()
    
    # Find current version
    version_match = re.search(r"__version__ = '(\d+)\.(\d+)\.(\d+)'", content)
    if not version_match:
        print("Could not find version in version.py")
        sys.exit(1)
    
    return version_match, content

def bump_version(version_type):
    version_match, content = get_version()
    major, minor, patch = map(int, version_match.groups())
    
    # Bump version according to input
    if version_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif version_type == 'minor':
        minor += 1
        patch = 0
    elif version_type == 'patch':
        patch += 1
    else:
        print("Invalid version type. Use 'major', 'minor', or 'patch'")
        sys.exit(1)
    
    new_version = f"{major}.{minor}.{patch}"
    current_version = f"{version_match.group(1)}.{version_match.group(2)}.{version_match.group(3)}"
    print(f"Bumping version from {current_version} to {new_version}")
    
    # Replace version in version.py
    new_content = re.sub(
        r"__version__ = '(\d+)\.(\d+)\.(\d+)'",
        f"__version__ = '{new_version}'",
        content
    )
    
    with open(VERSION_PATH, 'w') as f:
        f.write(new_content)
    
    print(f"Updated version in tools/version.py to {new_version}")
    return new_version

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ['major', 'minor', 'patch']:
        print("Usage: python bump_version.py [major|minor|patch]")
        sys.exit(1)
    
    bump_version(sys.argv[1])