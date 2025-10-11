import subprocess
import sys
import os
from typing import Tuple


def check_opentrons_installation() -> bool:
    """
    Check if the opentrons module is properly installed.
    
    Returns:
        bool: True if opentrons is installed and opentrons_simulate is available
    """
    try:
        # Check if we can import the opentrons module
        import opentrons  # noqa: F401
        
        # Check if opentrons_simulate command is available
        command = ["opentrons_simulate.exe"] if sys.platform == "win32" else ["opentrons_simulate"]
        result = subprocess.run(command + ["--help"], 
                              capture_output=True, 
                              timeout=10)
        return result.returncode == 0
        
    except (ImportError, subprocess.TimeoutExpired, FileNotFoundError):
        return False
    
def run_opentrons_simulation(script_path: str, verbose: bool = True) -> Tuple[bool, str, str]:
    """
    Run the Opentrons simulation program on a given script.
    
    Args:
        script_path (str): Path to the protocol file to simulate
        verbose (bool): Whether to print output to console (default: True)
    
    Returns:
        Tuple[bool, str, str]: (success, stdout, stderr)
            - success: True if simulation ran successfully, False otherwise
            - stdout: Standard output from the simulation
            - stderr: Standard error from the simulation
    
    Raises:
        FileNotFoundError: If the script file doesn't exist
        RuntimeError: If opentrons module is not installed
    """
    
    # Check if script file exists
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Protocol file not found: {script_path}")
    
    # Convert to absolute path for clarity
    script_path = os.path.abspath(script_path)
    
    # Determine the correct command based on operating system
    if sys.platform == "win32":
        command = ["opentrons_simulate.exe", script_path]
    else:  # macOS, Linux, and other Unix-like systems
        command = ["opentrons_simulate", script_path]
    
    try:
        # Run the simulation
        if verbose:
            print(f"Running simulation for: {script_path}")
            print(f"Command: {' '.join(command)}")
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        success = result.returncode == 0
        stdout = result.stdout
        stderr = result.stderr
        
        if verbose:
            if success:
                print("✓ Simulation completed successfully")
            else:
                print("✗ Simulation failed")
            
            if stdout:
                print("--- Simulation Output ---")
                print(stdout)
            
            if stderr:
                print("--- Simulation Errors ---")
                print(stderr)
        
        return success, stdout, stderr
        
    except subprocess.TimeoutExpired:
        error_msg = "Simulation timed out after 5 minutes"
        if verbose:
            print(f"✗ {error_msg}")
        return False, "", error_msg
        
    except FileNotFoundError:
        error_msg = ("opentrons_simulate command not found. "
                    "Make sure you have installed the opentrons module: "
                    "pip install opentrons")
        if verbose:
            print(f"✗ {error_msg}")
        raise RuntimeError(error_msg)
        
    except Exception as e:
        error_msg = f"Unexpected error during simulation: {str(e)}"
        if verbose:
            print(f"✗ {error_msg}")
        return False, "", error_msg


print(check_opentrons_installation())

run_opentrons_simulation("test_simulation.py")