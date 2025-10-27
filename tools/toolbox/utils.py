from google.protobuf.struct_pb2 import Struct
import typing as t
import subprocess
import platform

def struct_to_dict(struct: Struct) -> t.Any:
    out = {}
    for key, value in struct.items():
        if isinstance(value, Struct):
            out[key] = struct_to_dict(value)
        else:
            out[key] = value
    return out


def text_to_speech(text: str) -> bool:
    """
    Convert text to speech using native system commands.
    
    Args:
        text (str): The text to speak
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    system = platform.system().lower()
    
    try:
        if system == "darwin":  # macOS
            # Use the 'say' command
            cmd = ["say", text]
            subprocess.run(cmd, check=True)
            return True
            
        elif system == "windows":
            # Use PowerShell with SAPI
            ps_script = (
                f"$s=New-Object -ComObject Sapi.SpVoice;"
                f"$s.Speak(\"{text}\")"
            )
            
            cmd = ["powershell", "-Command", ps_script]
            subprocess.run(cmd, check=True)
            return True
            
        else:
            print(f"Unsupported operating system: {system}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error running TTS command: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
