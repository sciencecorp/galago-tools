from telnetlib import Telnet
import logging
from typing import Union

def try_utf_decode(data:Union[str,bytes]) -> str:
    if isinstance(data, str):
        return data
    data_string = ""
    try:
        data_string = data.decode("utf-8")
    except Exception:
        raise Exception(f"error decoding to utf8 string: {data!r}")
    return data_string


def telnet_read(conn: Telnet, timeout: int=1) -> str:
    reply_string = conn.read_until(b"\r\n", timeout=timeout)
    reply = try_utf_decode(reply_string)

    if len(reply) < 2 or reply[-1] != "\n" or reply[-2] != "\r":
        raise Exception(f"Received invalid message {reply} from tcp connection.")

    logging.info(f"Received {reply[0:-2]}")

    return reply[0:-2]

class Pf400TcpIp:
    def __init__(self, tcp_host: str, tcp_port: int) -> None:
        self.conn = None
        try:
            self.conn = Telnet(tcp_host, tcp_port, timeout=1)
            self.write_and_read("mode")
        except Exception as e:
            logging.error(f"Failed to establish connection: {e}")
            if self.conn:
                try:
                    self.conn.close()
                except Exception as close_error:
                    logging.warning(f"Error closing connection: {close_error}")
                self.conn = None
            raise

    # PF400 should always return a single line of output, unless you are in "pc" mode.
    def read(self, timeout: int=5) -> str:
        if not self.conn:
            raise Exception("No active connection")
        return telnet_read(self.conn, timeout)

    def read_all(self) -> list[str]:
        if not self.conn:
            raise Exception("No active connection")
        messages = []

        more = True

        while more:
            try:
                msg = self.read(timeout=1)
                messages.append(msg)
            except Exception:
                more = False

        return messages

    def write(self, msg: str) -> None:
        if not self.conn:
            raise Exception("No active connection")
        logging.info(f"Sending {msg}")
        self.conn.write((msg + "\n").encode("utf-8"))

    def write_and_expect(self, msg: str, expected: str="0", timeout: int=5) -> None:
        if not self.conn:
            raise Exception("No active connection")
        command_name = msg.split(" ")[0]

        self.write(msg)
        result = self.read(timeout)

        if result != expected:
            raise Exception(f"Robot returned {result} for {command_name}. Expected {expected}")

    # Does NOT validate return value.
    def write_and_read(self, msg: str, timeout: int=5) -> str:
        if not self.conn:
            raise Exception("No active connection")
        self.write(msg)
        return self.read(timeout)

    def wait_for_eom(self) -> None:
        if not self.conn:
            raise Exception("No active connection")
        self.write("waitForEom")
        result = self.read(timeout=150)

        if result != "0":
            raise Exception(f"Robot returned {result} for waitForEom")

    def close(self) -> None:
        if self.conn:
            try:
                self.write_and_read("attach 0")
                self.conn.close()
            except Exception as e:
                logging.warning(f"Error closing connection: {e}")
            self.conn = None