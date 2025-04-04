import subprocess 
import os 
import logging 
import typing as t

def write_to_file(file_name: str, content: str) -> None:
    with open(file_name, "w") as f:
        f.write(content)

def run_python_script(script_content: str, blocking: bool = True) -> t.Optional[str]:
    #Create a temporary file to run the script
    if os.path.exists("tmp_file.py"):
        os.remove("tmp_file.py")
    if os.path.exists("stdout.txt"):
        os.remove("stdout.txt")
    temp_file = "tmp_file.py"
    #script_content = script_content.encode("utf-8").decode("unicode_escape")
    # Use a raw string to avoid escape sequence issues
    # This preserves all whitespace and newlines as they are
    script_content = r"{}".format(script_content)
    write_to_file(temp_file, script_content)

    if not os.path.exists(temp_file):
        raise RuntimeError("Invalid file path")
    cmd = ["python", "-m", temp_file.replace(".py", "").lstrip("/").replace("/", ".")]
    logging.info("Command: " + str(cmd))
    try:
        process = subprocess.Popen(cmd, stdout=open('stdout.txt', 'w'),stderr=subprocess.STDOUT)
        if blocking:
            process.wait()
            if process.returncode != 0:
                with open('stdout.txt', 'r') as f:
                    error_output = f.read()
                raise RuntimeError(f"Script failed with return code {process.returncode}. Output:\n{error_output}")
            else:
                with open('stdout.txt', 'r') as f:
                    return f.read()
    except FileNotFoundError:
        logging.error("Python executable not found.")
        raise
    except subprocess.CalledProcessError as e:
        logging.error(f"There was an error while running script: {e}")
        raise
    finally:
        logging.info("Cleaning up temporary files")
        os.remove(temp_file)
        os.remove('stdout.txt')
    return None


if __name__ == "__main__":
    print(run_python_script('print("Hello Worldaaaa")\nfor i in range(0,40):print(i)',blocking=True)) 