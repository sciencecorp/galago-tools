import subprocess
import os
import logging
import typing as t
import tempfile
import shutil


def write_to_file(file_name: str, content: str) -> None:
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(content)


def find_python_executable() -> str:
    """
    Find the Python executable, trying python3 first (for macOS/Linux),
    then falling back to python (for Windows).
    """
    # Try python3 first (macOS, Linux)
    try:
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            logging.info("Found python3 executable")
            return "python3"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Try python (Windows, or systems with python symlink)
    try:
        result = subprocess.run(
            ["python", "--version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            logging.info("Found python executable")
            return "python"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Check common paths as last resort
    common_paths = [
        "/usr/bin/python3",
        "/usr/local/bin/python3",
        "/opt/homebrew/bin/python3",
        "C:\\Python310\\python.exe",
        "C:\\Python39\\python.exe",
        "C:\\Python38\\python.exe",
    ]
    for path in common_paths:
        if os.path.isfile(path):
            logging.info(f"Found python at {path}")
            return path
    
    raise RuntimeError(
        "Python executable not found. Please ensure Python 3 is installed and in your PATH. "
        "On macOS/Linux, 'python3' should be available. On Windows, 'python' should be available."
    )


def run_python_script(
    script_content: str, 
    blocking: bool = True,
    python_exe: t.Optional[str] = None
) -> t.Optional[str]:

    # If no explicit python_exe provided, find one automatically
    if python_exe:
        python_executable = python_exe
        # Validate the executable exists if a full path was provided
        if not os.path.isfile(python_exe):
            raise RuntimeError(f"Python executable not found: {python_exe}")
    else:
        python_executable = find_python_executable()
    
    logging.info(f"Using python executable: {python_executable}")
    
    # Create temporary directory and files
    temp_dir = tempfile.mkdtemp()
    temp_script = os.path.join(temp_dir, "temp_script.py")
    stdout_file = os.path.join(temp_dir, "stdout.txt")
    
    try:
        write_to_file(temp_script, script_content)
        cmd = [python_executable, temp_script]
        
        # Execute script
        with open(stdout_file, 'w', encoding='utf-8') as f:
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT
            )
            
            if blocking:
                process.wait()
                with open(stdout_file, 'r', encoding='utf-8') as output_f:
                    output = output_f.read()
                if process.returncode != 0:
                    raise RuntimeError(
                        f"Script failed with return code {process.returncode}. Output:\n{output}"
                    )
                
                return output
            
            return None
            
    except FileNotFoundError:
        raise RuntimeError(f"Python executable not found: {python_executable}")
    except Exception as e:
        logging.error(f"Error while running script: {e}")
        raise
    finally:
        # Cleanup temporary files
        logging.info("Cleaning up temporary files")
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logging.warning(f"Failed to cleanup temporary directory: {e}")

