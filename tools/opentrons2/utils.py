import subprocess
import sys
import os
from typing import Tuple
import logging 
import tempfile
import json

def check_opentrons_installation() -> bool:
    """
    Check if the opentrons module is properly installed.
    
    Returns:
        bool: True if opentrons is installed and opentrons_simulate is available
    """
    import importlib.util
    
    try:
        # Check if we can import the opentrons module
        if importlib.util.find_spec("opentrons") is None:
            return False
        
        # Check if opentrons_simulate command is available
        command = ["opentrons_simulate.exe"] if sys.platform == "win32" else ["opentrons_simulate"]
        result = subprocess.run(command + ["--help"], 
                              capture_output=True, 
                              timeout=10)
        return result.returncode == 0
        
    except (subprocess.TimeoutExpired, FileNotFoundError):
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

def create_executable_script(self, script_content: str, variables: dict) -> str:
    """
    Create an executable script by injecting variables at the top of the script.
    """
    # Create the variables definition section
    variables_section = "# Injected variables\n"
    
    for key, var_data in variables.items():
        # Extract the actual variable name and value from the variable data structure
        if isinstance(var_data, dict) and 'name' in var_data and 'value' in var_data:
            var_name = var_data['name']
            raw_value = var_data['value']
            var_type = var_data.get('type', 'string')
            
            # Parse the value based on its type
            if var_type == 'array':
                # Parse JSON array string
                try:
                    parsed_value = json.loads(raw_value)
                    variables_section += f'{var_name} = {repr(parsed_value)}\n'
                except json.JSONDecodeError:
                    logging.warning(f"Failed to parse array variable {var_name}: {raw_value}")
                    variables_section += f'{var_name} = []\n'
                    
            elif var_type == 'boolean':
                # Parse boolean string
                bool_value = raw_value.lower() in ('true', '1', 'yes', 'on')
                variables_section += f'{var_name} = {bool_value}\n'
                
            elif var_type == 'number':
                # Parse number string
                try:
                    if '.' in str(raw_value):
                        parsed_value = float(raw_value)
                    else:
                        parsed_value = int(raw_value)
                    variables_section += f'{var_name} = {parsed_value}\n'
                except (ValueError, TypeError):
                    logging.warning(f"Failed to parse number variable {var_name}: {raw_value}")
                    variables_section += f'{var_name} = 0\n'
                    
            elif var_type == 'string':
                variables_section += f'{var_name} = "{raw_value}"\n'
                
            else:
                # Fallback for unknown types
                variables_section += f'{var_name} = "{raw_value}"\n'
                
        else:
            # Handle case where key is the variable name and var_data is the direct value
            var_name = str(key)
            if isinstance(var_data, str):
                variables_section += f'{var_name} = "{var_data}"\n'
            elif isinstance(var_data, (list, dict)):
                variables_section += f'{var_name} = {repr(var_data)}\n'
            else:
                variables_section += f'{var_name} = {var_data}\n'
    
    variables_section += "\n# End injected variables\n\n"
    
    # Combine variables with the script content
    processed_script = variables_section + script_content
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
        f.write(processed_script)
        logging.info(f"Created executable script: {f.name}")
        return f.name

