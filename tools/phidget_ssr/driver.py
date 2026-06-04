from tools.base_server import ABCToolDriver

import logging
import typing as t


class PhidgetSSRDriver(ABCToolDriver):
    """Driver for the Phidget REL1100 4-channel solid state relay on a VINT hub.

    Each relay is a Phidget22 DigitalOutput channel (0..3); PWM is controlled via
    setDutyCycle (0.0-1.0). The phidget22 library is imported lazily inside the
    methods so importing this module (for `galago --info` introspection and for
    tests that mock the driver) does not require the native library to be present.

    The REL1100 is output-only and cannot sense the physical load, so the readback
    in set_duty_cycle confirms the controller setpoint, not that current flowed.
    """

    NUM_CHANNELS = 4
    DUTY_TOLERANCE = 0.01

    def __init__(
        self,
        hub_port: int = 0,
        serial_number: t.Optional[int] = None,
        frequency: t.Optional[float] = None,
        attach_timeout_ms: int = 5000,
    ) -> None:
        self.hub_port = hub_port
        self.serial_number = serial_number
        self.frequency = frequency
        self.attach_timeout_ms = attach_timeout_ms
        self.channels: list[t.Any] = []

    def _make_attach_handler(self, channel: int) -> t.Callable[..., None]:
        def on_attach(handle: t.Any) -> None:
            logging.info(f"Phidget SSR channel {channel} attached (hub_port={self.hub_port})")
        return on_attach

    def _make_detach_handler(self, channel: int) -> t.Callable[..., None]:
        def on_detach(handle: t.Any) -> None:
            logging.warning(f"Phidget SSR channel {channel} detached (hub_port={self.hub_port})")
        return on_detach

    def _make_error_handler(self, channel: int) -> t.Callable[..., None]:
        def on_error(handle: t.Any, code: int, description: str) -> None:
            logging.error(f"Phidget SSR channel {channel} error {code}: {description}")
        return on_error

    def _apply_frequency(self, output: t.Any, channel: int) -> None:
        from Phidget22.PhidgetException import PhidgetException  # type: ignore

        try:
            output.setFrequency(self.frequency)
            logging.info(f"Phidget SSR channel {channel} frequency set to {self.frequency} Hz")
        except PhidgetException as e:
            raise RuntimeError(
                f"Failed to set frequency {self.frequency} Hz on channel {channel}: {e} "
                f"(requires firmware >=120 and a value within the device range)"
            ) from e

    def initialize(self) -> None:
        from Phidget22.Devices.DigitalOutput import DigitalOutput  # type: ignore

        self.channels = []
        try:
            for channel in range(self.NUM_CHANNELS):
                output = DigitalOutput()
                output.setIsHubPortDevice(False)
                output.setHubPort(self.hub_port)
                output.setChannel(channel)
                if self.serial_number is not None:
                    output.setDeviceSerialNumber(self.serial_number)
                output.setOnAttachHandler(self._make_attach_handler(channel))
                output.setOnDetachHandler(self._make_detach_handler(channel))
                output.setOnErrorHandler(self._make_error_handler(channel))
                output.openWaitForAttachment(self.attach_timeout_ms)
                # Frequency is a per-channel property in Phidget22; apply the one configured value to each.
                if self.frequency is not None:
                    self._apply_frequency(output, channel)
                self.channels.append(output)
            logging.info(
                f"Initialized Phidget SSR: {self.NUM_CHANNELS} channels on hub_port "
                f"{self.hub_port} (serial={self.serial_number})"
            )
        except Exception:
            # Close any channels opened before the failure so we leak no handles.
            self.close()
            raise

    def set_duty_cycle(self, channel: int, duty_cycle: float) -> None:
        output = self.channels[channel]
        # Synchronous call: raises PhidgetException if it can't reach the device.
        output.setDutyCycle(duty_cycle)
        readback = output.getDutyCycle()
        if abs(readback - duty_cycle) > self.DUTY_TOLERANCE:
            raise RuntimeError(
                f"Phidget SSR channel {channel} duty cycle mismatch: "
                f"requested {duty_cycle}, controller reports {readback}"
            )
        logging.info(
            f"Phidget SSR channel {channel} duty cycle confirmed at the controller: {readback}"
        )

    def close(self) -> None:
        for channel, output in enumerate(getattr(self, "channels", [])):
            try:
                output.setDutyCycle(0.0)
                output.close()
            except Exception as e:
                logging.warning(f"Phidget SSR channel {channel} failed to close cleanly: {e}")
        self.channels = []

    def __del__(self) -> None:
        """Best-effort cleanup when the driver is destroyed."""
        try:
            self.close()
        except Exception:
            pass


if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.DEBUG)
    driver = PhidgetSSRDriver(hub_port=0)
    try:
        driver.initialize()
        for channel in range(PhidgetSSRDriver.NUM_CHANNELS):
            logging.info(f"Testing channel {channel}")
            driver.set_duty_cycle(channel, 0.25)
            time.sleep(0.5)
            driver.set_duty_cycle(channel, 1.0)
            time.sleep(0.5)
            driver.set_duty_cycle(channel, 0.0)
    except Exception as e:
        logging.error(f"Error during Phidget SSR test: {e}")
    finally:
        driver.close()
