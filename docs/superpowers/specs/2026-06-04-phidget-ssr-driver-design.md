# PhidgetSSR Driver & Server — Design

**Date:** 2026-06-04
**Branch:** `clariostar-and-lcus1` (never commit to `main`)
**Author:** Alberto Nava (with Claude)

## 1. Goal

Add a galago tool for the **Phidget REL1100_0** — a 4-channel isolated solid
state relay — connected through a **Phidget HUB0007_0** (1-port VINT hub) over
USB. The tool must drive **PWM (duty cycle) on each of the 4 channels
independently** and be fully compatible with galago, on both Windows and macOS.

Design principles: rigorous and robust, but simple (grug — no complexity that
isn't needed). The tool follows the existing driver/server conventions in this
repo, modeled most closely on `tools/lcus1_relay/`.

## 2. Hardware & library facts (verified)

- The REL1100 is an **intelligent VINT device**. Each relay is a Phidget22
  `DigitalOutput` channel, addressed by `setIsHubPortDevice(False)`,
  `setHubPort(<port>)`, `setChannel(0..3)`, and optionally
  `setDeviceSerialNumber(<hub serial>)`.
- PWM: `setDutyCycle(float)` in range **0.0–1.0** (Min=0, Max=1, ~0.1%
  resolution). `setState(bool)` exists for plain on/off but is not exposed (see
  §4 — PWM-only command surface).
- Frequency: `setFrequency(float)` supported on firmware ≥120; controller range
  **100 Hz–20 kHz**. Optional; applied once at connect.
- `openWaitForAttachment(timeout)` — **timeout in milliseconds**.
- **Output state persists after `close()`** — the driver must zero each channel
  before closing.
- The pip package `phidget22` **bundles the native library for Windows, Linux,
  and macOS**, so `pip install phidget22` is sufficient on both target OSes; no
  separate driver install is required for a VINT device like the REL1100.
- The REL1100 is **output-only**: no current/voltage sensing. `getDutyCycle()`
  returns the *commanded setpoint*, not a measurement of the physical load.

## 3. File layout (matches `lcus1_relay`)

- `tools/phidget_ssr/driver.py` — `PhidgetSSRDriver`
- `tools/phidget_ssr/server.py` — `PhidgetSSRServer`
- `tools/tests/phidget_ssr_test.py` — unit tests
- `interfaces/tools/grpc_interfaces/phidget_ssr.proto` — proto definition
- No `__init__.py` (consistent with `tools/lcus1_relay/`).

Tool name / `toolType`: **`phidget_ssr`** (snake_case, like `lcus1_relay`).

## 4. Proto — `phidget_ssr.proto`

PWM-only command surface. On/off is achieved with duty cycle 1.0 / 0.0.

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
  uint32 hub_port = 1;             // default 0
  optional int32 serial_number = 2; // optional; disambiguates the hub
  optional float frequency = 3;     // optional PWM Hz; applied to all channels at connect
}
```

### Wiring into the shared protos

- `interfaces/tools/grpc_interfaces/tool_base.proto`:
  - add `import "tools/grpc_interfaces/phidget_ssr.proto";`
  - Command oneof: `tools.grpc_interfaces.phidget_ssr.Command phidget_ssr = 23;`
  - Config oneof: `tools.grpc_interfaces.phidget_ssr.Config phidget_ssr = 42;`
- `interfaces/controller.proto`: add `phidget_ssr = 23;` to `ToolType`.
- Regenerate with `bin/make proto` (generated `*_pb2*` files are gitignored).

## 5. Driver — `PhidgetSSRDriver(ABCToolDriver)`

`phidget22` is **lazy-imported inside the driver methods**, not at module top,
so importing the module (for `galago --info`/`--list` introspection in
`tools/utils.py`, and for tests that mock the driver) never requires the native
library to be present.

Constructor:

```python
def __init__(self, hub_port: int = 0, serial_number: Optional[int] = None,
             frequency: Optional[float] = None, attach_timeout_ms: int = 5000) -> None
```

`NUM_CHANNELS = 4`. `DUTY_TOLERANCE = 0.01` (readback comparison; comfortably
above the device's ~0.1% resolution).

**`initialize()`**
1. Lazy-import `DigitalOutput` (and `PhidgetException` for error wrapping).
2. For `ch_index` in `0..3`: create a `DigitalOutput`; set
   `setIsHubPortDevice(False)`, `setHubPort(hub_port)`, `setChannel(ch_index)`,
   and `setDeviceSerialNumber(serial_number)` if provided; attach log-only
   handlers (see §7); `openWaitForAttachment(attach_timeout_ms)`; if `frequency`
   is set, apply `setFrequency(frequency)` wrapped so failure raises a clear
   error (firmware <120 or out-of-range → `Configure` fails visibly). Append to
   `self.channels`.
3. If any channel fails mid-loop, close the channels already opened, then
   re-raise — no leaked open handles.
4. Log the device serial / hub port and (if read successfully) the actual
   frequency via `getFrequency()`.

**`set_duty_cycle(channel: int, duty_cycle: float)`**
1. `self.channels[channel].setDutyCycle(duty_cycle)` — synchronous; raises
   `PhidgetException` on delivery failure (this is the real delivery guarantee).
2. Read back `getDutyCycle()`; if `abs(readback - duty_cycle) > DUTY_TOLERANCE`,
   raise `RuntimeError` with a clear message; otherwise log a confirmation line.
   Logging states "duty cycle confirmed at the controller" — **not** that the
   physical load is energized (the SSR has no sensing).

**`close()`** — for each open channel, best-effort `setDutyCycle(0.0)` then
`close()`, each guarded so one bad channel does not prevent the others from
closing. `__del__` calls `close()` defensively (guarded by `getattr`/try so a
failed `initialize()` cannot raise during garbage collection).

## 6. Server — `PhidgetSSRServer(ToolServer)`

`toolType = "phidget_ssr"`.

**`_configure(config)`** — close any existing driver, then build:
```python
self.driver = PhidgetSSRDriver(
    hub_port=config.hub_port,
    serial_number=config.serial_number if config.HasField("serial_number") else None,
    frequency=config.frequency if config.HasField("frequency") else None,
)
self.driver.initialize()
```

**`SetDutyCycle(params) -> Optional[ExecuteCommandReply]`**
- Validate `0 <= channel < 4` and `0.0 <= duty_cycle <= 1.0`; on failure return
  `ExecuteCommandReply(response=INVALID_ARGUMENTS, error_message=..., return_reply=True)`.
- On success: `self.driver.set_duty_cycle(channel, duty_cycle)`, return `None`.
- `EstimateSetDutyCycle(params) -> int`: return `1`.

**`TimedDutyCycle(params) -> Optional[ExecuteCommandReply]`**
- Validate channel, duty cycle, and `duration_seconds > 0` (same
  `INVALID_ARGUMENTS` pattern; mirrors `lcus1_relay.TimedSwitch`).
- On success: `set_duty_cycle(channel, duty_cycle)`, `time.sleep(duration)`,
  `finally` force `set_duty_cycle(channel, 0.0)`. Return `None`.
- `EstimateTimedDutyCycle(params) -> int`: return `math.ceil(duration_seconds)`.

`__main__` mirrors `lcus1_relay/server.py`: argparse `--port`, then
`serve(PhidgetSSRServer(), str(args.port))`.

## 7. Observability & verification (grug-approved: no concurrency in control path)

- **Log-only event handlers** on each channel: `setOnAttachHandler`,
  `setOnDetachHandler`, `setOnErrorHandler`, wired before
  `openWaitForAttachment`. They **only call `logging`** (include the channel
  index via a small closure). They never touch `self.channels` or server state,
  so the fact that they fire on the Phidget library thread introduces no
  concurrency hazard. They surface USB unplug / hub power loss / async errors.
- **Delivery confirmation** comes free from the synchronous API: `setDutyCycle`
  raises on failure and the base server reports `DRIVER_ERROR` with the message.
- **Setpoint readback** (see §5) gives an explicit per-command confirmation,
  honestly framed as a controller setpoint check, not load sensing.
- **Explicitly out of scope** (deliberate simplicity): event-driven control flow,
  command queues, retry loops, and auto-updating server status on detach. The
  blocking API already covers the control path; detach→status coupling can be
  added later if a real need appears.

## 8. Dependencies

Add `phidget22` to root `requirements.txt` (cross-platform; the wheel bundles
the native lib for Windows and macOS). No per-tool requirements file is used in
this repo, matching how `pyserial` is declared for `lcus1_relay`.

## 9. Error handling summary

| Condition | Result |
|---|---|
| Bad channel / duty out of range / non-positive duration | `INVALID_ARGUMENTS` reply (server-level) |
| Device not attached / comms failure during a command | `PhidgetException` propagates → `DRIVER_ERROR` |
| Attach timeout or bad frequency at connect | exception in `_configure` → status `FAILED` with message |
| Readback diverges from setpoint | `RuntimeError` → `DRIVER_ERROR` |
| `close()` on a bad channel | logged warning; other channels still close |

## 10. Testing — `tools/tests/phidget_ssr_test.py`

Mirrors `lcus1_relay_test.py`: instantiate the server, set `self.driver =
MagicMock()`, `simulated = False`, `status = READY`. Tests:

- `SetDutyCycle` routes to `driver.set_duty_cycle(channel, duty)`; returns `None`.
- `SetDutyCycle` rejects channel `> 3`, channel out of range, duty `< 0`, duty
  `> 1` → `INVALID_ARGUMENTS`, driver not called.
- `TimedDutyCycle` (with `time.sleep` patched) calls set→sleep→set(0.0); rejects
  zero / negative duration and bad channel/duty; forces channel to 0.0 even when
  `sleep` raises.
- `EstimateSetDutyCycle == 1`; `EstimateTimedDutyCycle == ceil(duration)`.

Tests run on macOS and Windows without hardware (driver is mocked; `phidget22`
not required because of the lazy import). Real-hardware validation happens on the
Windows laptop with the REL1100 attached.

## 11. Out of scope / non-goals

- No `SetState` / on-off command (PWM-only surface; use duty 1.0 / 0.0).
- No `SetAllDutyCycles` bulk command.
- No per-command frequency control (frequency is config-time only).
- No event-driven control flow (see §7).
