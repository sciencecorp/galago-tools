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
