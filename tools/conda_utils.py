
import os 
import subprocess 
import logging 

def check_conda_is_path() -> bool:
    if os.name != 'nt':
        raise RuntimeError("This method is meant to be used on a windows machine only")
    cmd = "conda"
    try:
        process = subprocess.Popen(cmd,stdout=subprocess.PIPE)
        process.communicate()[0]
        return True
    except Exception as e:
        logging.error(f"Failed to call conda command. {e}")
        return False

def conda_activate(env_name:str) -> bool:
    if os.name != 'nt':
        raise RuntimeError("This method is meant to be used on a windows machine only")

    cmd = ["conda","activate",env_name]
    try:
        process = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True)
        response = process.communicate()[0]
        logging.info(response)
        return True
    except Exception as e:
        logging.error(f"Failed to call conda command. {e}")
        return False
    
def get_conda_environments() -> list[str]:
    if os.name != 'nt':
        raise RuntimeError("This method is meant to be used on a windows machine only")
    conda_is_path = check_conda_is_path()
    paths = []
    if conda_is_path:
        cmd = ["conda","info","--envs"]
        process = subprocess.Popen(cmd,stdout=subprocess.PIPE)
        response = process.communicate()[0]
        decoded_string = response.decode('utf-8')
        lines = decoded_string.split('\r\n')
        for line in lines:
            splitted_line = line.split()
            if len(splitted_line) > 1:
                if splitted_line[0] == "#":
                    continue
                env_name = splitted_line[0]
                paths.append(env_name)

        return paths
    else:
        return paths
