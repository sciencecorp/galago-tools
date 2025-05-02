#!/usr/bin/env python
"""
Usage: python bump_version.py [major|minor|patch]
Bumps the version in setup.py according to semver rules.
"""

import re
import sys
import os

def bump_version(version_type):
    # Read setup.py
    setup_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'setup.py')
    with open(setup_path, 'r') as f:
        content = f.read()
    
    # Find current version
    version_match = re.search(r"version='(\d+)\.(\d+)\.(\d+)'", content)
    if not version_match:
        print("Could not find version in setup.py")
        sys.exit(1)
    
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
    print(f"Bumping version from {version_match.group(1)}.{version_match.group(2)}.{version_match.group(3)} to {new_version}")
    
    # Replace version in setup.py
    new_content = re.sub(
        r"version='(\d+)\.(\d+)\.(\d+)'", 
        f"version='{new_version}'", 
        content
    )
    
    with open(setup_path, 'w') as f:
        f.write(new_content)
    
    print(f"Updated version in setup.py to {new_version}")
    return new_version

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ['major', 'minor', 'patch']:
        print("Usage: python bump_version.py [major|minor|patch]")
        sys.exit(1)
    
    bump_version(sys.argv[1]) 