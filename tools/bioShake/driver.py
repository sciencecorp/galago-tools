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
        self.connect()

    def __del__(self) -> None:
        self.disconnect()

    def _send_command(self, command: str) -> str:
        if not self.ser.is_open:
            self.ser.open()

        full_command = command + "\r\n"
        logging.debug(f"Sending command: {command}")
        self.ser.write(full_command.encode("ascii"))

        response = self.ser.readline().decode("ascii").strip()
        logging.debug(f"Received response: {response}")

        if response == "e":
            error_list = self.get_error_list()
            raise Exception("BioShake error: " + error_list)
        return response

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

    def connect(self) -> None:
        if not self.ser.is_open:
            self.ser.open()
        else:
            self.reset_device()
            self.ser.close()
            self.ser.open()

    def disconnect(self) -> None:
        if self.ser.is_open:
            self.ser.close()

    def _is_clamp_locked(self) -> bool:
        elm_state = self.get_elm_state_as_string()
        if elm_state.lower() == "elmlocked":
            return True
        else:
            return False

    def grip(self) -> None:
        self._send_command("selp")

    def ungrip(self) -> None:
        if self._get_shake_state() != "Home":
            self.home()
            # Wait a bit to be sure the device has homed.
            while self._get_shake_state() != "Home":
                time.sleep(0.1)
        self._send_command("seup")

    def home(self) -> None:
        if not self._is_clamp_locked():
            self.grip()
        self._send_command("sgh")
        while self._get_shake_state() != "Home":
            time.sleep(0.1)

    def start_shake(self, speed: int, duration: int) -> None:
        if not self._is_clamp_locked():
            self.grip()

        current_speed_str = self._send_command("gsts")
        try:
            current_speed = float(current_speed_str)
        except ValueError:
            logging.error("Invalid shake speed received.")
            return

        if int(current_speed) == 0:
            logging.error(f"Shake speed is: {current_speed}. Please set to a positive nonzero value!")
        else:
            self._send_command("son")
        # (Duration handling could be added here if desired.)

    def stop_shake(self) -> None:
        self._send_command("soff")

    def reset(self) -> None:
        self._send_command("reset")

    def wait_for_shake(self) -> None:
        while self._get_shake_state() != "Home":
            time.sleep(0.1)

    def _set_shake_speed(self, speed: int) -> None:
        if 0 < speed < 999999:
            self._send_command("ssts" + str(speed))
        else:
            logging.error("Please enter a valid target speed. (Non-negative and no larger than 6 digits.)")

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

    def temp_on(self) -> None:
        self._send_command("ton")

    def temp_off(self) -> None:
        self._send_command("toff")

    def _set_temp(self, temp: int) -> None:
        if 0 < temp < 990:
            self._send_command("stt" + str(temp))
        else:
            logging.error(f"Enter a valid temperature target {temp/10}. Must be a three digit number in the range 0-99.")

    def get_elm_state_as_string(self) -> str:
        return self._send_command("gesas")

    def set_elm_lock_pos(self) -> None:
        self.grip()

    def set_elm_unlock_pos(self) -> None:
        self.ungrip()

    def set_shake_target_speed(self, rpm: int) -> None:
        self._set_shake_speed(rpm)

    def shake_on_with_runtime(
        self, seconds: int, speed: t.Optional[int] = None, acceleration: t.Optional[int] = None
    ) -> None:
        if not self._is_clamp_locked():
            self.grip()
        if speed is not None:
            self._set_shake_speed(speed)
        if acceleration is not None:
            self._set_acceleration(acceleration)
        else:
            self._set_acceleration(10)
        self._send_command("sonwr" + str(seconds))
        while self._get_shake_state() != "Home":
            time.sleep(0.1)
        self.ungrip()

    def get_shake_remaining_time(self) -> int:
        return self._get_remaining_time()

    def shake_off(self) -> None:
        self.stop_shake()

    # For compatibility with the blank template.
    def shake_with_time(self, duration: int, speed: int) -> None:
        self.shake_on_with_runtime(seconds=duration, speed=speed)


if __name__ == "__main__":
    try:
        logging.basicConfig(
            level=logging.DEBUG,  # Set the logging level (DEBUG, INFO, etc.)
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        driver = BioshakeDriver(port="COM7")
        driver.connect()
        print("version: ", driver.get_version())
        print("ELM state: ", driver.get_elm_state_as_string())
        print("locking...")
        driver.set_elm_lock_pos()
        print("Shake state: ", driver._get_shake_state())
        print("setting target speed to 200...")
        driver.set_shake_target_speed(rpm=200)
        print("start shaking for 10 seconds...")
        driver.shake_on_with_runtime(seconds=10)
        for i in range(5):
            print("Remaining time: ", driver.get_shake_remaining_time())
            time.sleep(1)
        print("stop shaking...")
        driver.shake_off()
        shake_state = driver._get_shake_state()
        print("Shake state: ", shake_state)
        if shake_state == "ELMLocked":
            print("unlocking...")
            driver.set_elm_unlock_pos()
        print("resetting device...")
        driver.reset()
    finally:
        driver.disconnect()
