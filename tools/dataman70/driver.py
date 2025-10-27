import logging
import serial
from typing import Union, Optional
from tools.toolbox.variables import update_variable 
from tools.base_server import ABCToolDriver

READ_TIMEOUT = 5  # Increased timeout for scan operations

def try_utf_decode(data: Union[str, bytes]) -> str:
    """Convert bytes to UTF-8 string if needed."""
    if isinstance(data, str):
        return data
    try:
        return data.decode("utf-8")
    except Exception:
        raise serial.SerialException(f"Error decoding to UTF-8: {data!r}")


class Dataman70Driver(ABCToolDriver):
    def __init__(self, com_port: str, timeout: int = READ_TIMEOUT) -> None:
        """Initialize the barcode scanner driver.
        
        Args:
            com_port: Serial port path (e.g., '/dev/ttyUSB0' or 'COM3')
            timeout: Read timeout in seconds
        """
        self.serial_port = serial.Serial(
            com_port, 
            baudrate=9600,  # Common baudrate for barcode scanners
            timeout=timeout,
            write_timeout=1
        )
        logging.info(f"Connected to Dataman70 on {com_port}")

    def close(self) -> None:
        """Close the serial connection."""
        if self.serial_port.is_open:
            # Disable scanning before closing
            try:
                self.serial_port.write(b"||>SET TRIGGER.TYPE 0\r\n")
                logging.info("Disabled scanning mode")
            except Exception as e:
                logging.error(f"Error disabling scanning mode: {e}")
            
            self.serial_port.close()
            logging.info("Dataman70 connection closed")

    def _read_response(self) -> str:
        """Read a response from the scanner."""
        self.serial_port.reset_input_buffer()
        reply = self.serial_port.read_until(expected=b"\n")
        reply_string = try_utf_decode(reply)
        
        if not reply_string:
            return ""
            
        # Check for proper line ending (should end with \r\n)
        if reply_string.endswith("\r\n"):
            return reply_string[:-2]  # Remove \r\n
        elif reply_string.endswith("\n"):
            return reply_string[:-1]  # Remove \n
        
        return reply_string.strip()


    def assert_barcode(self, expected: str) -> None:
        """Scan and assert that the scanned barcode matches the expected value.
        Args:
            expected: The expected barcode string  
        """
        scanned = self.scan_barcode()
        if scanned is None:
            logging.error("No barcode scanned")
            raise RuntimeError("No barcode detected")
        if scanned == expected:
            logging.info(f"Scanned barcode matches expected: {scanned}")
            return None
        else:
            logging.warning(f"Scanned barcode '{scanned}' does not match expected '{expected}'")
            raise RuntimeError(f"Barcode mismatch: expected '{expected}', got '{scanned}'")

    def scan_barcode(self, mapped_variable: Optional[str]=None) -> Optional[str]:
        """Trigger a barcode scan and return the result.
        
        Returns:
            The scanned barcode as a string, or None if no barcode was scanned
            
        Raises:
            serial.SerialException: If there's a communication error
            Exception: If the scanner is not responding
        """
        try:
            # Enable scanning (trigger type 1)
            self.serial_port.write(b"||>SET TRIGGER.TYPE 1\r\n")
            
            # Read the barcode data
            barcode = self._read_response()
            # Always disable scanning after attempt (trigger type 0)
            self.serial_port.write(b"||>SET TRIGGER.TYPE 0\r\n")
            
            if barcode and len(barcode) > 1:  # Valid barcode (more than 1 character)
                logging.info(f"Scanned barcode: {barcode}")
                if mapped_variable:
                    update_variable(mapped_variable, barcode)
                    logging.info(f"Updated variable '{mapped_variable}' with scanned barcode")
                return barcode
            
            logging.warning("No barcode detected or scan timeout")
            return None
            
        except serial.SerialException as e:
            logging.error(f"Serial communication error: {e}")
            # Try to disable scanning even on error
            try:
                self.serial_port.write(b"||>SET TRIGGER.TYPE 0\r\n")
            except Exception as e:
                raise RuntimeError("Failed to disable scanning after communication error")
            raise
        except Exception as e:
            logging.error(f"Unexpected error during scan: {e}")
            # Try to disable scanning even on error
            try:
                self.serial_port.write(b"||>SET TRIGGER.TYPE 0\r\n")
            except Exception as e:
                raise RuntimeError("Failed to disable scanning after error")
            raise

    def __exit__(self) -> None:
        """Context manager exit - ensures connection is closed."""
        self.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    driver = Dataman70Driver("/dev/tty.usbmodem1A1727PP2448261")  # Update with actual port
    try:
        barcode = driver.scan_barcode("barcsode")
    finally:
        driver.close()
