import sys
import logging
import typing as t
import os
from concurrent import futures
import time
import grpc
from google.protobuf import message
from tools.grpc_interfaces import tool_base_pb2, tool_driver_pb2_grpc, tool_driver_pb2
from typing import Optional
import logging.handlers
from grpc_reflection.v1alpha import reflection

if sys.platform == 'win32':
    import ctypes
    windll = ctypes.windll
else:
    windll = None

# Configure logging to use the socket handler
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', 
)


class ABCToolDriver:
    """
    The ABCToolDriver is a dummy class, which responds to any method call with a
    None, and logs the call.
    """
    def __getattr__(self, name: str) -> t.Callable:
        return lambda *args, **kwargs: None

    def kill_processes(self, process_name: str, ask_user:bool=True) -> None:
        # check if any processes are running (length of returned list is > 0)
        if len([proc_str for proc_str in os.popen('tasklist').readlines() if proc_str.startswith(process_name)]) > 0:
            return_val = 1
            if ask_user:
                # ask user with pop whether or not to kill processes
                style_flag = 0x00001124 # 1 -> sys modal,no; 1 -> default to NO button; 2 -> add ? icon, 4 -> yes/no button style
                if windll:
                    windll.user32.MessageBoxW(0, f"Kill running {process_name} processes?", f"Kill {self.__class__} Processes", style_flag)
                else:
                    print(f"Kill running {process_name} processes?")
                
            # if "OK" then kill 'em
            if return_val == 1:
                logging.info("ABCToolDriver Killing Previously Active %s processes", process_name)
                while len([proc_str for proc_str in os.popen('tasklist').readlines() if proc_str.startswith(process_name)]) > 0:
                    os.system(f"taskkill /f /im {process_name}")

class ToolServer(tool_driver_pb2_grpc.ToolDriverServicer):
    toolType: str
    toolId: str  = "undefined"

    def _configure(self, request: t.Any) -> None:
        # Up to the tool to configure itself
        raise NotImplementedError()
        
    def __init__(self) -> None:
        self.driver: t.Optional[ABCToolDriver] = ABCToolDriver()
        self.start_time: float = time.time()
        self.status: tool_base_pb2.ToolStatus = tool_base_pb2.NOT_CONFIGURED
        self.last_error : Optional[str] = ""
        self.setSimulated(False)
        self.is_connected : bool = False

    def GetStatus(
        self, request: tool_base_pb2.Config, context: grpc.ServicerContext
    ) -> tool_base_pb2.StatusReply:
     
        return tool_base_pb2.StatusReply(
            uptime=int(time.time() - self.start_time),
            status=tool_base_pb2.SIMULATED if self.simulated else self.status,
            error_message = self.last_error
        )

    # In future, our drivers should probably have a way of running in a
    # "simulated" mode that still verifies things like arguments and whatnot
    def setSimulated(self, simulated: bool) -> None:
        self.simulated = simulated

    def setStatus(self, status: tool_base_pb2.ToolStatus) -> None:
        # logging.info(f"Setting status to {str(status)}")
        self.status = status
    
    def Configure(
        self, request: tool_base_pb2.Config, context: grpc.ServicerContext
    ) -> tool_base_pb2.ConfigureReply:
        logging.info(f"Received configuration: {request}")
        self.config = getattr(request, request.WhichOneof("config"))
        
        if request.toolId:
            self.toolId = request.toolId
        
        if not request.simulated and self.simulated:
            self.setSimulated(request.simulated)
            self.setStatus(self.status)
            return tool_base_pb2.ConfigureReply(response=tool_base_pb2.SUCCESS)
        
        else:
            try:
                if request.simulated:
                    self.setSimulated(request.simulated)
                    return tool_base_pb2.ConfigureReply(response=tool_base_pb2.SUCCESS)
                self._configure(self.config)
                self.setStatus(tool_base_pb2.READY)
                self.last_error = ""
                self.is_connected = True
                return tool_base_pb2.ConfigureReply(response=tool_base_pb2.SUCCESS)
            except Exception as e:
                self.setStatus(tool_base_pb2.FAILED)
                self.last_error = str(e)
                logging.error(f"Failed to configure Tool={self.toolId}-{str(e)}")
                self.is_connected = False 
                return tool_base_pb2.ConfigureReply(
                    response=tool_base_pb2.NOT_READY, error_message=str(e)
                )

    def _dispatchCommand(
        self, command: message.Message
    ) -> tool_base_pb2.ExecuteCommandReply:
        # We use the class name which follows the convection CommandName, which
        # neatly maps to the casing convention the gRPC code uses for "public"
        # commands. For the tool, this is the "public" interface in some sense - we
        # could even imagine generating a gRPC type for it.
        method_name = command.__class__.__name__
        try:
            method = getattr(self, method_name)
        except AttributeError as e:
            logging.error(str(e))
            self.last_error = "Unrecognized command"
            return tool_base_pb2.ExecuteCommandReply(
                response=tool_base_pb2.UNRECOGNIZED_COMMAND
            )
        if self.simulated:
            duration, error = self._estimateDuration(command)
            if error is not None:
                return tool_base_pb2.ExecuteCommandReply(response=error, return_reply=True)
            if method_name != "RunProgram":
                #logging.debug(f"Sleeping for estimated duration: {duration}")
                time.sleep(float(duration if duration else 0))
                return tool_base_pb2.ExecuteCommandReply(response=tool_base_pb2.SUCCESS, return_reply=True)
            else:
                try:
                    response_tmp = method(command, simulated=True)
                    #logging.debug(f"Simulated response: {response_tmp}")
                    if response_tmp is None:
                        response = tool_base_pb2.ExecuteCommandReply(
                            response=tool_base_pb2.SUCCESS,
                            return_reply=True
                        )
                    else:
                        response = tool_base_pb2.ExecuteCommandReply(
                            response=response_tmp.response,
                            error_message=response_tmp.error_message,
                            return_reply=response_tmp.return_reply,
                        )
                    return response
                except KeyError as e:
                    logging.debug(f"Simulated error: {str(e)}")
                    return tool_base_pb2.ExecuteCommandReply(
                        response=tool_base_pb2.INVALID_ARGUMENTS, error_message=str(e), return_reply=True
                    )
        else:
            try:
                response_tmp = method(command)
                if response_tmp is None:
                    response = tool_base_pb2.ExecuteCommandReply(
                        response=tool_base_pb2.SUCCESS
                    )
                    self.last_error = ""
                else:
                    response = tool_base_pb2.ExecuteCommandReply(
                        response=response_tmp.response,
                        meta_data=response_tmp.meta_data,
                        error_message=response_tmp.error_message,
                        return_reply=response_tmp.return_reply,
                    )
                    self.last_error = response_tmp.error_message 
                return response
            except KeyError as e:
                logging.error(str(e))
                self.last_error = str(e)
                return tool_base_pb2.ExecuteCommandReply(
                    response=tool_base_pb2.INVALID_ARGUMENTS, error_message=str(e)
                )

    def runSequence(self, sequence: list[message.Message]) -> None:
        for command in sequence:
            self._dispatchCommand(command)

    def isReady(self) -> bool:
        if self.simulated:
            return True
        return self.status == tool_base_pb2.READY

    def parseCommand(
        self, request: tool_base_pb2.Command
    ) -> tuple[t.Any, t.Any, Optional[str]]:
        if not self.isReady():
            return None, tool_base_pb2.NOT_READY, None

        command = None
        try:
            tool_name = request.WhichOneof("tool_command")
            if tool_name != self.toolType:
                return None, tool_base_pb2.WRONG_TOOL, None
            tool_command = getattr(request, tool_name)

            command_name = tool_command.WhichOneof("command")
            if command_name is None:
                return None, tool_base_pb2.UNRECOGNIZED_COMMAND, None
            command = getattr(tool_command, command_name)
        except ValueError as e:
            logging.error(str(e))
            return None, tool_base_pb2.INVALID_ARGUMENTS, str(e)

        return command, None, None

    def ExecuteCommand(
        self, request: tool_base_pb2.Command, context: grpc.ServicerContext
    ) -> tool_base_pb2.ExecuteCommandReply:
        # logging.info(f"Received command: {str(request)}:100.100")
        sys.stdout.flush()
        command, error, error_msg = self.parseCommand(request)

        if error is not None:
            logging.error(f"Failed o execute commad for Tool {self.toolId}, Error={error_msg}")
            self.last_error = error_msg
            return tool_base_pb2.ExecuteCommandReply(
                response=error, error_message=error_msg
            )

        if command is not None:
            try:
                logging.debug("Setting tool to BUSY")
                self.setStatus(tool_base_pb2.BUSY)
                logging.info(f"Running command {command.__class__.__name__}")
                response = self._dispatchCommand(command)
                logged_response = str(response)
                logged_response = (logged_response[:100] + '...') if len(logged_response) > 100 else logged_response
                logging.debug(f"ExecuteCommand Response: {str(logged_response)}")
                return response
            except Exception as e:
                logging.error(f"Error on Tool ={self.toolId}")
                self.last_error = str(e)
                return tool_base_pb2.ExecuteCommandReply(
                    response=tool_base_pb2.DRIVER_ERROR, error_message=str(e)
                )
            finally:
                self.setStatus(tool_base_pb2.READY)
                # logging.info(f"Setting {self.toolId} to READY")
        return tool_base_pb2.ExecuteCommandReply(response=tool_base_pb2.SUCCESS)

    def _estimateDuration(self, command: message.Message) -> tuple[Optional[int], t.Any]:
        method_name = f"Estimate{command.__class__.__name__}"
        try:
            method = getattr(self, method_name)
        except AttributeError as e:
            logging.error(str(e))
            return None, tool_base_pb2.UNRECOGNIZED_COMMAND

        return method(command), None

    def EstimateDuration(
        self, request: tool_base_pb2.Command, context: grpc.ServicerContext
    ) -> tool_base_pb2.EstimateDurationReply:
        command, error, error_msg = self.parseCommand(request)
        if error is not None:
            return tool_base_pb2.EstimateDurationReply(
                response=error, error_message=error_msg
            )

        if command is None:
            return tool_base_pb2.EstimateDurationReply(
                response=error, error_message=error_msg
            )

        try:
            duration, error = self._estimateDuration(command)
            if error is not None:
                return tool_base_pb2.EstimateDurationReply(response=error)
            else:
                return tool_base_pb2.EstimateDurationReply(
                    response=tool_base_pb2.SUCCESS, estimated_duration_seconds=duration
                )
        except Exception as e:
            logging.error(str(e))
            return tool_base_pb2.EstimateDurationReply(
                response=tool_base_pb2.DRIVER_ERROR, error_message=str(e)
            )

def serve(tool_server: 'ToolServer', port: str, num_workers: int = 10) -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=num_workers))
    
    # Register your service.
    tool_driver_pb2_grpc.add_ToolDriverServicer_to_server(tool_server, server)
    
    # Get the service name from the correct module.
    try:
        service_name = tool_driver_pb2.DESCRIPTOR.services_by_name["ToolDriver"].full_name
    except KeyError:
        raise RuntimeError("Service name 'ToolDriver' not found in descriptor. "
                           "Please check your proto definition.")
    
    service_names = [
        service_name,
        reflection.SERVICE_NAME,
    ]
    reflection.enable_server_reflection(service_names, server)
    
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logging.info(f"{tool_server.toolType} server started, listening on {port}")
    server.wait_for_termination()