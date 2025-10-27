import serial
import time
import logging
import typing as t

from tools.base_server import ABCToolDriver

ERROR_CODES = {
            "101": "DC motor controller error.",
            "102": "Error caused by speed failure (e.g mechanical locking).",
            "103": "Shaker not initialized or initialization parameters were incorrect after powering on.",
            "104": "Initialization error.",
            "105": "Shaker did not home after stop command.",
            "201": "Error due to failed response from temperature sensors or incorrect internal settings of temperature sensors.",
            "202": "Temperature communication bus error.",
            "203": "Sensor with the requested ID was not found.",
            "204": "Errors caused by a faulty temperature measurement during run.",
            "300": "General error.",
            "301": "IC-Driver error.",
            "303": "Verification error by the unlock position. Please RESTART the system.",
            "304": "Error caused by unsuccessful reach the lock position (timeout). Please RESTART the system.",
            "305": "Error caused by unsuccessful reach the unlock position (timeout). Please RESTART the system.",
            "306": "Error caused by unsuccessful reach the lock position (over current). Please RESTART the system.",
            "307": "Error caused by unsuccessful reach the unlock position (over current). Please RESTART the system.",
        }

SHAKE_STATES = {
                "0": "Shaking",
                "1": "Shake Cycle Stopped and Homed",
                "2": "Shake Cycle Emergency Stop. Re-home shaker",
                "3": "Home",
                "4": "Manual Mode",
                "5": "Accelerating",
                "6": "Decelerate",
                "7": "Decelerate to Stop.",
                "90": "ECO Mode.",
                "99": "Boot Process Running.",
            }

class BioshakeDriver(ABCToolDriver):
    def __init__(self, port: str):
        self.port = port
        self.ser = serial.Serial(port, baudrate=9600, timeout=3)
        self.shake_state = None

    def __del__(self) -> None:
        self.disconnect()

    def _send_command(self, command: str) -> str:
        if not self.ser.is_open:
            self.ser.open()

        full_command = command + "\r\n"
        self.ser.write(full_command.encode("ascii"))
        response = self.ser.readline().decode("ascii").strip()
        if response == "e":
            error_list = self.get_error_list()
            if not error_list:
                error_list = "Unknown error - no error codes returned from device"
            error_msg = f"BioShake error during command '{command}': {error_list}"
            logging.error(error_msg)
            raise Exception(error_msg)
        return response

    """
    Initialization commands 
    """

    def connect(self) -> None:
        if self.ser is not None and self.ser.is_open:
            logging.warning("Already connected to the device...")
            return None
        try:
            self.ser = serial.Serial(port=self.port, baudrate=9600, timeout=1)
        except serial.SerialException as e:
            logging.error(f"Error opening serial port: {e}")
            raise

    def disconnect(self) -> None:
        if self.ser.is_open:
            self.ser.close()

    def reset(self) -> None:
        self._send_command("reset")
        attempts: int = 0
        while attempts < 5:
            try:
                if self.ser:
                    self.disconnect()
                    logging.info("Device reset successfully.")
                    self.ser.open()
                    break
                else:
                    self.connect()
                    break
            except serial.SerialException:
                attempts += 1
                time.sleep(1)
        if attempts == 5:
            logging.error("Failed to reset device after multiple attempts.")    
            raise Exception("Failed to reset device.")

    def get_version(self) -> str:
        version = self._send_command("v")
        if version is None:
            logging.error("Failed to get version.")
            return "Unknown"
        return version.strip()

    def get_error_list(self) -> str:
        result = self._send_command("gel").strip()
        errors = []
        for err in result.split(";"):
            code = err.strip().strip("{}")
            if code in ERROR_CODES:
                errors.append(ERROR_CODES[code])
            else:
                errors.append(code)
        error_message = "\n".join(errors)
        logging.error("Error list: " + error_message)
        return error_message

    def flash_led(self) -> None:
        self._send_command("fled")

    """Shake Commmands"""
    def home(self) -> None:
        if not self.is_gripper_closed():
            self.grip()
        self._send_command("sgh")
        while self._get_shake_state() != "Home":
            time.sleep(0.5)

    def stop_shake(self) -> None:
        self._send_command("soff")
        while self._get_shake_state() != "Home":
            time.sleep(0.5)
        self.ungrip()

    def _set_shake_speed(self, speed: int) -> None:
        if 0 < speed < 9999:
            self._send_command("ssts" + str(speed))
        else:
            raise ValueError("Please enter a valid target speed. (Non-negative and no larger than 4 digits.)")

    def _set_acceleration(self, acceleration: int) -> None:
        if 0 < acceleration <= 99:
            self._send_command("ssa" + str(acceleration))
        else:
            logging.error("Please enter an acceleration value within a 1 to 2 digit range.")

    def _get_remaining_time(self) -> int:
        response = self._send_command("gsrt")
        try:
            return int(response)
        except ValueError:
            logging.error("Invalid remaining time received.")
            return 0

    def _get_shake_state(self) -> str:

        result = self._send_command("gsst")
        if result in SHAKE_STATES:
            return SHAKE_STATES[result]
        elif result is None:
            return "Unable to return Shaker status"
        return result

    def _get_target_speed(self) -> int:
        response = self._send_command("gsts")
        try:
            return int(response)
        except ValueError:
            logging.error("Invalid target speed received.")
            return 0

    def _get_speed_actual(self) -> int:
        response = self._send_command("gsas")
        try:
            return int(response)
        except ValueError:
            logging.error("Invalid actual speed received.")
            return 0

    def _get_acceleration_actual(self) -> int:
        response = self._send_command("gsa")
        try:
            return int(response)
        except ValueError:
            logging.error("Invalid acceleration value received.")
            return 0



    """Gripper Commmands"""
    def is_gripper_closed(self) -> bool:
        elm_state = self.get_elm_state_as_string()
        if elm_state.lower() == "elmlocked":
            return True
        else:
            return False

    def grip(self) -> None:
        self._send_command("selp")

    def ungrip(self) -> None:
        self._send_command("seup")

    def start_shake(self, speed: t.Optional[int] = None, acceleration: t.Optional[int] = None
    ) -> None:
        if not self.is_gripper_closed():
            self.grip()
        if speed is not None:
            self._set_shake_speed(speed)
        if acceleration is not None:
            self._set_acceleration(acceleration)
        
        self._send_command("son")

    def get_elm_state_as_string(self) -> str:
        return self._send_command("gesas")

    def set_elm_lock_pos(self) -> None:
        self.grip()

    def set_elm_unlock_pos(self) -> None:
        self.ungrip()
    
    def wait_for_shake(self, timeout: int) -> None:
        start_time = time.time()
        while time.time() - start_time < timeout:
            shake_state = self._get_shake_state()
            if shake_state == "Home":
                logging.info("Shake finished")
                return None
            time.sleep(0.5)
        
        raise TimeoutError(f"Shake operation timed out after {timeout} seconds")
    
    
    def set_shake_target_speed(self, rpm: int) -> None:
        self._set_shake_speed(rpm)

    def shake_on_with_runtime(
        self, seconds: int, speed: t.Optional[int] = None, acceleration: t.Optional[int] = None
    ) -> None:
        if not self.is_gripper_closed():
            self.grip()
        if speed is not None:
            self._set_shake_speed(speed)
        if acceleration is not None:
            self._set_acceleration(acceleration)
        else:
            self._set_acceleration(10)
        self._send_command("sonwr" + str(seconds))
        while self._get_shake_state() != "Home":
            time.sleep(0.5)
        self.ungrip()

    def get_shake_remaining_time(self) -> int:
        return self._get_remaining_time()


    """Temperature Commmands"""
    def temp_on(self) -> None:
        self._send_command("ton")

    def temp_off(self) -> None:
        self._send_command("toff")

    def set_tmp(self, temp: int) -> None:
        if 0 < temp < 990:
            self._send_command("stt" + str(temp))
        else:
            logging.error(f"Enter a valid temperature target {temp}. Must be a three digit number in the range 0-999.")

