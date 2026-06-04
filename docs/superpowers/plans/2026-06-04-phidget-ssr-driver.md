# PhidgetSSR Driver & Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a galago tool (`phidget_ssr`) that drives PWM duty cycle on each of the 4 channels of a Phidget REL1100 solid state relay, connected via a HUB0007 VINT hub over USB, on both Windows and macOS.

**Architecture:** Follows the existing `tools/lcus1_relay/` driver/server convention. A `PhidgetSSRDriver(ABCToolDriver)` wraps the Phidget22 `DigitalOutput` API (one channel per relay, lazy-imported so the module loads without the native lib). A `PhidgetSSRServer(ToolServer)` exposes PWM-only commands (`SetDutyCycle`, `TimedDutyCycle`) with argument validation and setpoint readback verification. Log-only attach/detach/error handlers add observability without adding concurrency to the control path.

**Tech Stack:** Python 3.9, gRPC/protobuf, `phidget22` (cross-platform pip wheel bundling the native lib), `unittest` + `pytest`.

**Spec:** `docs/superpowers/specs/2026-06-04-phidget-ssr-driver-design.md`

**Branch:** `clariostar-and-lcus1` — never commit to `main`. End every commit message with the `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` trailer.

---

## Task 1: Proto definition and wiring

**Files:**
- Create: `interfaces/tools/grpc_interfaces/phidget_ssr.proto`
- Modify: `interfaces/tools/grpc_interfaces/tool_base.proto`
- Modify: `interfaces/controller.proto`

- [ ] **Step 1: Create the proto file**

Create `interfaces/tools/grpc_interfaces/phidget_ssr.proto`:

```proto
syntax = 'proto3';

package com.science.foundry.tools.grpc_interfaces.phidget_ssr;

message Command {
  oneof command {
    SetDutyCycle set_duty_cycle = 1;
    TimedDutyCycle timed_duty_cycle = 2;
  }

  message SetDutyCycle {
    uint32 channel = 1;       // 0..3
    float duty_cycle = 2;     // 0.0..1.0
  }

  message TimedDutyCycle {
    uint32 channel = 1;       // 0..3
    float duty_cycle = 2;     // 0.0..1.0
    float duration_seconds = 3;
  }
}

message Config {
  uint32 hub_port = 1;              // default 0
  optional int32 serial_number = 2; // optional; disambiguates the hub
  optional float frequency = 3;     // optional PWM Hz; applied to all channels at connect
}
```

- [ ] **Step 2: Add the import to `tool_base.proto`**

In `interfaces/tools/grpc_interfaces/tool_base.proto`, find:

```proto
import "tools/grpc_interfaces/clariostar.proto";
```

Add immediately after it:

```proto
import "tools/grpc_interfaces/phidget_ssr.proto";
```

- [ ] **Step 3: Add to the Command oneof in `tool_base.proto`**

Find:

```proto
    tools.grpc_interfaces.lcus1_relay.Command lcus1_relay = 22;
```

Add immediately after it:

```proto
    tools.grpc_interfaces.phidget_ssr.Command phidget_ssr = 23;
```

- [ ] **Step 4: Add to the Config oneof in `tool_base.proto`**

Find:

```proto
    tools.grpc_interfaces.lcus1_relay.Config lcus1_relay = 41;
```

Add immediately after it:

```proto
    tools.grpc_interfaces.phidget_ssr.Config phidget_ssr = 42;
```

- [ ] **Step 5: Add to the `ToolType` enum in `controller.proto`**

In `interfaces/controller.proto`, find:

```proto
  lcus1_relay = 22;
```

Add immediately after it:

```proto
  phidget_ssr = 23;
```

- [ ] **Step 6: Regenerate the protobuf Python files**

Run: `bin/make proto`
Expected: completes without error; creates `tools/grpc_interfaces/phidget_ssr_pb2.py`, `phidget_ssr_pb2.pyi`, `phidget_ssr_pb2_grpc.py`, and regenerates `tool_base_pb2.py` / `controller_pb2.py`.

- [ ] **Step 7: Verify the generated messages import and wire correctly**

Run:
```bash
python -c "from tools.grpc_interfaces.phidget_ssr_pb2 import Command, Config; from tools.grpc_interfaces.tool_base_pb2 import Command as TB; print(Command.SetDutyCycle(channel=2, duty_cycle=0.5)); print('phidget_ssr' in [f.name for f in TB.DESCRIPTOR.fields])"
```
Expected: prints the `SetDutyCycle` message and `True`.

- [ ] **Step 8: Commit**

```bash
git add interfaces/tools/grpc_interfaces/phidget_ssr.proto interfaces/tools/grpc_interfaces/tool_base.proto interfaces/controller.proto
git commit -m "Add phidget_ssr proto messages and wiring

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```
(Generated `*_pb2*` files are gitignored, so only the `.proto` files are committed.)

---

## Task 2: Add the phidget22 dependency

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add phidget22 to requirements**

In `requirements.txt`, find the line:

```
pyserial==3.5
```

Add immediately after it:

```
phidget22
```

(Left unpinned intentionally: the wheel bundles the platform/architecture-specific native library — notably the Apple-Silicon arm64 dylib — and we want the current build on each OS.)

- [ ] **Step 2: Install it locally**

Run: `python -m pip install phidget22`
Expected: installs successfully on macOS/Windows.

- [ ] **Step 3: Verify it imports**

Run: `python -c "from Phidget22.Devices.DigitalOutput import DigitalOutput; print('phidget22 OK')"`
Expected: prints `phidget22 OK`.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "Add phidget22 dependency for phidget_ssr tool

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: PhidgetSSR driver

This is hardware-facing code (cannot be unit-tested without the device). The automated check here verifies the module imports cleanly **without** `phidget22` (proving the lazy import works for tool introspection and for the mocked server tests). A `__main__` block provides a manual hardware smoke test for the Windows laptop.

**Files:**
- Create: `tools/phidget_ssr/driver.py`

- [ ] **Step 1: Create the driver**

Create `tools/phidget_ssr/driver.py`:

```python
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
        self.channels: list = []

    def _make_attach_handler(self, channel: int) -> t.Callable:
        def on_attach(handle: t.Any) -> None:
            logging.info(f"Phidget SSR channel {channel} attached (hub_port={self.hub_port})")
        return on_attach

    def _make_detach_handler(self, channel: int) -> t.Callable:
        def on_detach(handle: t.Any) -> None:
            logging.warning(f"Phidget SSR channel {channel} detached (hub_port={self.hub_port})")
        return on_detach

    def _make_error_handler(self, channel: int) -> t.Callable:
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
```

- [ ] **Step 2: Verify the module imports without the native lib loaded**

Run: `python -c "from tools.phidget_ssr.driver import PhidgetSSRDriver; d = PhidgetSSRDriver(hub_port=0); print(d.NUM_CHANNELS, d.DUTY_TOLERANCE)"`
Expected: prints `4 0.01` (constructing the driver must not trigger any Phidget22 import).

- [ ] **Step 3: Commit**

```bash
git add tools/phidget_ssr/driver.py
git commit -m "Add PhidgetSSR driver for REL1100 relay

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: PhidgetSSR server (TDD)

The server holds the galago-facing logic — command routing, argument validation, and the timed-PWM sequence. Tests mock the driver, so they run on any OS without hardware.

**Files:**
- Create: `tools/tests/phidget_ssr_test.py`
- Create: `tools/phidget_ssr/server.py`

- [ ] **Step 1: Write the failing tests**

Create `tools/tests/phidget_ssr_test.py`:

```python
import math
import unittest
from unittest.mock import MagicMock, call, patch

from tools.grpc_interfaces.phidget_ssr_pb2 import Command, Config
from tools.grpc_interfaces.tool_base_pb2 import INVALID_ARGUMENTS
from tools.phidget_ssr.server import PhidgetSSRServer


class TestSetDutyCycle(unittest.TestCase):
    def setUp(self) -> None:
        self.server = PhidgetSSRServer()
        self.server.driver = MagicMock()
        self.server.config = Config(hub_port=0)
        self.server.simulated = False
        self.server.status = 3  # READY

    def test_set_duty_cycle_routes_to_driver(self) -> None:
        params = Command.SetDutyCycle(channel=2, duty_cycle=0.5)
        result = self.server.SetDutyCycle(params)
        self.server.driver.set_duty_cycle.assert_called_once_with(2, 0.5)
        self.assertIsNone(result)

    def test_set_duty_cycle_rejects_channel_out_of_range(self) -> None:
        params = Command.SetDutyCycle(channel=4, duty_cycle=0.5)
        result = self.server.SetDutyCycle(params)
        self.assertEqual(result.response, INVALID_ARGUMENTS)
        self.server.driver.set_duty_cycle.assert_not_called()

    def test_set_duty_cycle_rejects_duty_above_one(self) -> None:
        params = Command.SetDutyCycle(channel=0, duty_cycle=1.5)
        result = self.server.SetDutyCycle(params)
        self.assertEqual(result.response, INVALID_ARGUMENTS)
        self.server.driver.set_duty_cycle.assert_not_called()

    def test_set_duty_cycle_rejects_negative_duty(self) -> None:
        params = Command.SetDutyCycle(channel=0, duty_cycle=-0.25)
        result = self.server.SetDutyCycle(params)
        self.assertEqual(result.response, INVALID_ARGUMENTS)
        self.server.driver.set_duty_cycle.assert_not_called()

    def test_estimate_set_duty_cycle(self) -> None:
        params = Command.SetDutyCycle(channel=0, duty_cycle=0.5)
        self.assertEqual(self.server.EstimateSetDutyCycle(params), 1)


class TestTimedDutyCycle(unittest.TestCase):
    def setUp(self) -> None:
        self.server = PhidgetSSRServer()
        self.server.driver = MagicMock()
        self.server.config = Config(hub_port=0)
        self.server.simulated = False
        self.server.status = 3  # READY

    @patch("tools.phidget_ssr.server.time.sleep")
    def test_timed_duty_cycle_sets_sleeps_then_zeroes(self, mock_sleep: MagicMock) -> None:
        params = Command.TimedDutyCycle(channel=1, duty_cycle=0.75, duration_seconds=5.0)
        result = self.server.TimedDutyCycle(params)
        self.server.driver.set_duty_cycle.assert_has_calls([call(1, 0.75), call(1, 0.0)])
        mock_sleep.assert_called_once_with(5.0)
        self.assertIsNone(result)

    @patch("tools.phidget_ssr.server.time.sleep", side_effect=Exception("unexpected"))
    def test_timed_duty_cycle_zeroes_on_exception(self, mock_sleep: MagicMock) -> None:
        params = Command.TimedDutyCycle(channel=1, duty_cycle=0.75, duration_seconds=10.0)
        with self.assertRaises(Exception):
            self.server.TimedDutyCycle(params)
        self.server.driver.set_duty_cycle.assert_has_calls([call(1, 0.75), call(1, 0.0)])

    def test_timed_duty_cycle_rejects_zero_duration(self) -> None:
        params = Command.TimedDutyCycle(channel=0, duty_cycle=0.5, duration_seconds=0.0)
        result = self.server.TimedDutyCycle(params)
        self.assertEqual(result.response, INVALID_ARGUMENTS)
        self.server.driver.set_duty_cycle.assert_not_called()

    def test_timed_duty_cycle_rejects_negative_duration(self) -> None:
        params = Command.TimedDutyCycle(channel=0, duty_cycle=0.5, duration_seconds=-1.0)
        result = self.server.TimedDutyCycle(params)
        self.assertEqual(result.response, INVALID_ARGUMENTS)
        self.server.driver.set_duty_cycle.assert_not_called()

    def test_timed_duty_cycle_rejects_bad_channel(self) -> None:
        params = Command.TimedDutyCycle(channel=9, duty_cycle=0.5, duration_seconds=5.0)
        result = self.server.TimedDutyCycle(params)
        self.assertEqual(result.response, INVALID_ARGUMENTS)
        self.server.driver.set_duty_cycle.assert_not_called()

    def test_estimate_timed_duty_cycle(self) -> None:
        params = Command.TimedDutyCycle(channel=0, duty_cycle=0.5, duration_seconds=3.7)
        self.assertEqual(self.server.EstimateTimedDutyCycle(params), math.ceil(3.7))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/tests/phidget_ssr_test.py -v`
Expected: collection error / FAIL — `ModuleNotFoundError: No module named 'tools.phidget_ssr.server'`.

- [ ] **Step 3: Implement the server**

Create `tools/phidget_ssr/server.py`:

```python
import argparse
import logging
import math
import time
import typing as t

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.phidget_ssr_pb2 import Command, Config
from tools.grpc_interfaces.tool_base_pb2 import ExecuteCommandReply, INVALID_ARGUMENTS

from .driver import PhidgetSSRDriver

NUM_CHANNELS = 4


class PhidgetSSRServer(ToolServer):
    toolType = "phidget_ssr"
    driver: PhidgetSSRDriver
    config: Config

    def __init__(self) -> None:
        super().__init__()

    def _configure(self, config: Config) -> None:
        self.config = config
        if self.driver:
            self.driver.close()
        self.driver = PhidgetSSRDriver(
            hub_port=config.hub_port,
            serial_number=config.serial_number if config.HasField("serial_number") else None,
            frequency=config.frequency if config.HasField("frequency") else None,
        )
        self.driver.initialize()

    def _invalid(self, message: str) -> ExecuteCommandReply:
        response = ExecuteCommandReply()
        response.response = INVALID_ARGUMENTS
        response.error_message = message
        response.return_reply = True
        return response

    def _validate(self, channel: int, duty_cycle: float) -> t.Optional[ExecuteCommandReply]:
        if not 0 <= channel < NUM_CHANNELS:
            return self._invalid(f"channel must be in 0..{NUM_CHANNELS - 1}, got {channel}")
        if not 0.0 <= duty_cycle <= 1.0:
            return self._invalid(f"duty_cycle must be in 0.0..1.0, got {duty_cycle}")
        return None

    def SetDutyCycle(self, params: Command.SetDutyCycle) -> t.Optional[ExecuteCommandReply]:
        error = self._validate(params.channel, params.duty_cycle)
        if error is not None:
            return error
        logging.info(f"SetDutyCycle channel={params.channel} duty_cycle={params.duty_cycle}")
        self.driver.set_duty_cycle(params.channel, params.duty_cycle)
        return None

    def EstimateSetDutyCycle(self, params: Command.SetDutyCycle) -> int:
        return 1

    def TimedDutyCycle(self, params: Command.TimedDutyCycle) -> t.Optional[ExecuteCommandReply]:
        error = self._validate(params.channel, params.duty_cycle)
        if error is not None:
            return error
        if params.duration_seconds <= 0:
            return self._invalid("duration_seconds must be greater than 0")
        logging.info(
            f"TimedDutyCycle channel={params.channel} duty_cycle={params.duty_cycle} "
            f"for {params.duration_seconds}s"
        )
        self.driver.set_duty_cycle(params.channel, params.duty_cycle)
        try:
            time.sleep(params.duration_seconds)
        finally:
            self.driver.set_duty_cycle(params.channel, 0.0)
        return None

    def EstimateTimedDutyCycle(self, params: Command.TimedDutyCycle) -> int:
        return math.ceil(params.duration_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    args = parser.parse_args()
    if not args.port:
        raise RuntimeWarning("Port must be provided...")
    serve(PhidgetSSRServer(), str(args.port))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tools/tests/phidget_ssr_test.py -v`
Expected: all 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/phidget_ssr/server.py tools/tests/phidget_ssr_test.py
git commit -m "Add PhidgetSSR server and tests

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Full lint / type / test verification

**Files:** none (verification only)

- [ ] **Step 1: Ruff**

Run: `ruff check tools/phidget_ssr/ tools/tests/phidget_ssr_test.py`
Expected: no errors.

- [ ] **Step 2: Mypy**

Run: `mypy --config-file=pyproject.toml tools/phidget_ssr/`
Expected: no errors (the lazy Phidget22 imports carry `# type: ignore`; `warn_unused_ignores` is False, so they are safe whether or not the lib is installed).

- [ ] **Step 3: Tool discovery / introspection sanity check**

Run: `galago --info phidget_ssr`
Expected: prints tool info listing the `SetDutyCycle` and `TimedDutyCycle` commands without error (proves the server module introspects without requiring hardware).

- [ ] **Step 4: Full test suite**

Run: `python -m pytest tools/tests/ -vv`
Expected: the existing suite plus the 11 new `phidget_ssr` tests PASS.

- [ ] **Step 5: Commit any fixes**

If steps 1–4 required changes, commit them:
```bash
git add -A
git commit -m "Fix lint/type issues for phidget_ssr

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```
If nothing changed, skip this step.

---

## Manual hardware validation (on the Windows laptop with the REL1100 attached)

Not part of the automated plan — run once on the real device:

1. `python -m tools.phidget_ssr.driver` — cycles each of the 4 channels through 0.25 → 1.0 → 0.0 duty and logs the confirmed readback per channel.
2. Confirm via the Phidget Control Panel is closed first (it locks the USB channel).
3. Optionally start the server: `galago-serve --port=50020 --tool=phidget_ssr` and configure it through galago with `hub_port=0`.
```

