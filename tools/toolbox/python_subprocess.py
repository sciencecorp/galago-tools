import subprocess
import os
import logging
import typing as t
import tempfile
import shutil


def write_to_file(file_name: str, content: str) -> None:
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(content)


def run_python_script(
    script_content: str, 
    blocking: bool = True,
    python_exe: t.Optional[str] = None
) -> t.Optional[str]:

    python_executable = python_exe if python_exe else "python"
    logging.info(f"Using python executable: {python_executable}")
    # Validate the executable exists if a full path was provided
    if python_exe and not os.path.isfile(python_exe):
        raise RuntimeError(f"Python executable not found: {python_exe}")
    
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

