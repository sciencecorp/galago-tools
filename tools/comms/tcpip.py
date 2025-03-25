import socket
import time
from typing import Optional

class TcpIp:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.is_connected = False

    def connect(self) -> None:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.ip, self.port))
            self.is_connected = True
        except Exception as e:
            raise Exception(f"Error establishing connection: {e}")

    def disconnect(self) -> None:
        try:
            if self.socket:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
        except Exception as e:
            raise Exception(f"Error closing connection: {e}")

    def clear_buffer(self) -> None:
        if self.socket:
            self.socket.setblocking(False)
            try:
                while self.socket.recv(1024):
                    pass
            except BlockingIOError:
                pass
            self.socket.setblocking(True)

    def send_command(self, message: str) -> str:
        if self.socket:
            self.socket.sendall(message.encode())
            response = self.socket.recv(1024).decode()
            time.sleep(0.5)
            return response
        return ""

    def read_response(self, buffer_size: int = 1024, timeout: float = 60) -> str:
        if self.socket:
            response_data = bytearray()
            self.socket.settimeout(timeout)
            try:
                while True:
                    chunk = self.socket.recv(buffer_size)
                    response_data.extend(chunk)
                    if len(chunk) < buffer_size:
                        break
                time.sleep(0.5)
                return response_data.decode()
            finally:
                self.socket.settimeout(None)
        return ""