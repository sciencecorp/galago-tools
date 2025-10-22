from datetime import datetime
import os
import logging
from enum import Enum 
from typing import Optional, Any
import sys 
import socket 

class LogType(Enum):
    ERROR = "ERROR",
    WARNING = "WARNING",
    DEBUG = "DEBUG",
    INFO = "INFO",
    PLATE_MOVE = "PLATE_MOVE",
    RUN_START = "RUN_START",
    RUN_END = "RUN_END",
    PLATE_READ = "PLATE_READ",

def get_local_ip() -> Any:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1" # Default local IP
    finally:
        s.close()
    return local_ip

def get_shell_command(tool_type:str, port:int) -> list:
    return [sys.executable, '-m', f'tools.{tool_type}.server', f'--port={port}']

def write_trace_log(log_path:Optional[str], log_type:LogType, tool:str,value:str) -> None:

    if not log_path:
        logging.warning("Log folder not configured")
    if log_path is None:
        return
    if not os.path.exists(log_path):
        try:
            os.makedirs(log_path)
        except Exception as e:
            logging.warning(f"Failed to create log folder. {e}")
            return
    file_folder= os.path.join(log_path, datetime.today().strftime('%Y-%m-%d'))
    if(os.path.exists(file_folder) is False):
        logging.debug("folder does not exist. creating folder")
        os.mkdir(file_folder)

    trace_file = os.path.join(file_folder, "trace_log.txt")
    error_file = os.path.join(file_folder, "error_log.txt")

    try:
        if os.path.exists(trace_file) is False:
            with open(trace_file, 'w+') as f:
                f.write('Time,Tool,Value\n')
        if(log_type == LogType.ERROR):
            if os.path.exists(error_file) is False:
                with open(error_file, 'w+') as f:
                    f.write('Time,Tool,Error\n')
    except Exception as e:
        logging.debug(e)
        return
    try:
        with open(trace_file, 'a') as f:
            f.write(str(datetime.today())+","+str(log_type.name)+","+tool+","+value+"\n")
        if log_type == LogType.ERROR:
            with open(error_file, 'a') as f:
                 f.write(str(datetime.today())+","+str(log_type.name)+","+tool+","+value+"\n")
    except Exception as e:
        logging.debug(e)
        return

def list_available_tools() -> list:
    import os
    import importlib
    import inspect
    from pkgutil import iter_modules
    
    tool_list = []
    tool_path = os.path.join(os.path.dirname(__file__))
    
    for module_info in iter_modules([tool_path]):
        module_name = module_info.name
        server_module_path = f"tools.{module_name}.server"
        
        try:
            # Try to import the server module from the tool directory
            server_module = importlib.import_module(server_module_path)
            
            # Check if any class in the server module inherits from ToolServer
            has_toolserver_subclass = False
            for name, obj in inspect.getmembers(server_module, inspect.isclass):
                # Check if the class is defined in this server module (not imported)
                if obj.__module__ == server_module_path:
                    # Get the method resolution order to check inheritance
                    for base_class in inspect.getmro(obj):
                        if base_class.__name__ == 'ToolServer' and base_class is not obj:
                            has_toolserver_subclass = True
                            break
                    if has_toolserver_subclass:
                        break
            
            if has_toolserver_subclass:
                tool_list.append(module_name)
                
        except ImportError:
            continue
        except Exception:
            continue 
    return tool_list


def get_tool_server_info(tool_name: str) -> dict:
    """
    Get detailed information about a specific tool server and its commands.
    
    Args:
        tool_name: The name of the tool (e.g., 'opentrons2', 'plateloc')
    
    Returns:
        Dictionary containing tool server information including commands and their parameters
    """
    import importlib
    import inspect
    from google.protobuf.message import Message
    
    try:
        # Import the server module
        server_module_path = f"tools.{tool_name}.server"
        server_module = importlib.import_module(server_module_path)
        
        # Import the corresponding protobuf module for Command types
        try:
            pb_module_path = f"tools.grpc_interfaces.{tool_name}_pb2"
            pb_module = importlib.import_module(pb_module_path)
            command_class = getattr(pb_module, 'Command', None)
        except ImportError:
            pb_module = None
            command_class = None
        
        # Find the ToolServer subclass
        tool_server_class = None
        for name, obj in inspect.getmembers(server_module, inspect.isclass):
            if obj.__module__ == server_module_path:
                for base_class in inspect.getmro(obj):
                    if base_class.__name__ == 'ToolServer' and base_class is not obj:
                        tool_server_class = obj
                        break
                if tool_server_class:
                    break
        
        if not tool_server_class:
            return {"error": f"No ToolServer subclass found in {server_module_path}"}
        
        # Get basic tool information
        tool_info = {
            "tool_name": tool_name,
            "class_name": tool_server_class.__name__,
            "module_path": server_module_path,
            "tool_type": getattr(tool_server_class, 'toolType', tool_name),
            "commands": {},
            "estimate_methods": {},
            "other_methods": {}
        }
        
        # Helper function to get protobuf message fields
        def get_protobuf_fields(message_class : type) -> list[str]:
            """Extract field names from a protobuf message class."""
            if not message_class or not issubclass(message_class, Message):
                return []
            
            # Method 1: Use DESCRIPTOR if available
            if hasattr(message_class, 'DESCRIPTOR'):
                try:
                    descriptor = message_class.DESCRIPTOR
                    return [field.name for field in descriptor.fields]
                except Exception:
                    pass
            
            # Method 2: Look for field number constants
            field_names = []
            for attr_name in dir(message_class):
                if attr_name.endswith('_FIELD_NUMBER'):
                    # Convert SCRIPT_CONTENT_FIELD_NUMBER -> script_content
                    field_name = attr_name[:-13].lower()  # Remove _FIELD_NUMBER
                    field_names.append(field_name)
            
            return field_names
        
        # Analyze all methods in the class
        for method_name, method_obj in inspect.getmembers(tool_server_class):
            if (method_name.startswith('_') or 
                not callable(method_obj)):
                continue  # Skip private methods and non-callables
                
            # Get method signature
            try:
                sig = inspect.signature(method_obj)
                params = list(sig.parameters.values())[1:]  # Skip 'self' parameter
            except (ValueError, TypeError):
                continue
            
            # Check if this is a command method (has params with Command type)
            command_param = None
            for param in params:
                if param.name == 'params' and param.annotation != inspect.Parameter.empty:
                    annotation = param.annotation
                    annotation_str = str(annotation)
                    
                    # Check if this is a protobuf Message subclass
                    is_command_type = False
                    try:
                        # Check if annotation is a class and subclass of Message
                        if (inspect.isclass(annotation) and 
                            issubclass(annotation, Message)):
                            is_command_type = True
                    except (TypeError, AttributeError):
                        # Fallback: check string representation
                        is_command_type = (
                            hasattr(annotation, '__module__') and 
                            annotation.__module__ and 
                            '_pb2' in annotation.__module__ and
                            'Command.' in annotation_str
                        )
                    
                    if is_command_type:
                        # Extract the command type name
                        if hasattr(annotation, '__qualname__'):
                            type_name = annotation.__qualname__
                        else:
                            type_name = annotation_str.split('.')[-1] if '.' in annotation_str else str(annotation)
                        
                        # Get fields using protobuf-specific methods
                        fields = get_protobuf_fields(annotation)
                        
                        command_param = {
                            "name": param.name,
                            "type": type_name,
                            "annotation": annotation_str,
                            "fields": fields
                        }
                        
                        break
            
            if command_param:
                tool_info["commands"][method_name] = {
                    "method_name": method_name,
                    "parameter": command_param,
                    "docstring": inspect.getdoc(method_obj),
                    "signature": str(sig)
                }
            elif method_name.startswith('Estimate'):
                # Estimate methods
                tool_info["estimate_methods"][method_name] = {
                    "method_name": method_name,
                    "return_type": str(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else "Unknown",
                    "signature": str(sig),
                    "docstring": inspect.getdoc(method_obj)
                }
            else:
                # Other public methods (skip some common inherited methods)
                if method_name not in ['__init__', '__class__', '__dict__', '__doc__', '__module__', '__weakref__']:
                    tool_info["other_methods"][method_name] = {
                        "method_name": method_name,
                        "signature": str(sig),
                        "docstring": inspect.getdoc(method_obj)
                    }
        
        # Get Command class information if available
        if command_class:
            tool_info["command_class_info"] = {
                "class_name": command_class.__name__,
                "available_commands": []
            }
            
            # Get all nested Command classes
            for attr_name in dir(command_class):
                if attr_name.startswith('_'):
                    continue
                    
                attr = getattr(command_class, attr_name)
                if inspect.isclass(attr) and issubclass(attr, Message):
                    fields = get_protobuf_fields(attr)
                    command_info = {
                        "name": attr_name,
                        "full_name": f"Command.{attr_name}",
                        "fields": fields
                    }
                    tool_info["command_class_info"]["available_commands"].append(command_info)
        
        return tool_info
        
    except ImportError as e:
        return {"error": f"Could not import tool '{tool_name}': {e}"}
    except Exception as e:
        return {"error": f"Error analyzing tool '{tool_name}': {e}"}

def print_tool_server_info(tool_name: str) -> None:
    """
    Print formatted information about a tool server.
    """
    info = get_tool_server_info(tool_name)
    
    if "error" in info:
        print(f"Error: {info['error']}")
        return
    
    print(f"\n=== Tool Server Information: {info['tool_name']} ===")
    print(f"Class Name: {info['class_name']}")
    print(f"Module Path: {info['module_path']}")
    print(f"Tool Type: {info['tool_type']}")
    
    if info.get('command_class_info'):
        cmd_class = info['command_class_info']
        print(f"\n--- Available Protobuf Commands ({len(cmd_class['available_commands'])}) ---")
        for cmd in cmd_class['available_commands']:
            fields_str = f" (fields: {', '.join(cmd['fields'])})" if cmd['fields'] else " (no fields)"
            print(f"• {cmd['name']}{fields_str}")
    
    print("\n" + "="*50)


if __name__ == "__main__":
    # print("Available tools:", list_available_tools())
    print_tool_server_info("pf400")