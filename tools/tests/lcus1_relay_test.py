import unittest
from unittest.mock import MagicMock, patch, call
import math

from tools.grpc_interfaces.lcus1_relay_pb2 import Command, Config
from tools.grpc_interfaces.tool_base_pb2 import INVALID_ARGUMENTS
from tools.lcus1_relay.server import Lcus1RelayServer


class TestTimedSwitch(unittest.TestCase):
    def setUp(self) -> None:
        self.server = Lcus1RelayServer()
        self.server.driver = MagicMock()
        self.server.config = Config(com_port="COM4")
        self.server.simulated = False
        self.server.status = 2  # READY

    @patch("tools.lcus1_relay.server.time.sleep")
    def test_timed_switch_calls_on_sleep_off(self, mock_sleep: MagicMock) -> None:
        params = Command.TimedSwitch(duration_seconds=5.0)
        result = self.server.TimedSwitch(params)
        self.server.driver.on.assert_called_once()
        mock_sleep.assert_called_once_with(5.0)
        self.server.driver.off.assert_called_once()
        self.server.driver.assert_has_calls([call.on(), call.off()])
        self.assertIsNone(result)

    @patch("tools.lcus1_relay.server.time.sleep", side_effect=Exception("unexpected"))
    def test_timed_switch_turns_off_on_exception(self, mock_sleep: MagicMock) -> None:
        params = Command.TimedSwitch(duration_seconds=10.0)
        with self.assertRaises(Exception):
            self.server.TimedSwitch(params)
        self.server.driver.on.assert_called_once()
        self.server.driver.off.assert_called_once()

    def test_timed_switch_rejects_zero_duration(self) -> None:
        params = Command.TimedSwitch(duration_seconds=0.0)
        result = self.server.TimedSwitch(params)
        self.assertEqual(result.response, INVALID_ARGUMENTS)
        self.server.driver.on.assert_not_called()

    def test_timed_switch_rejects_negative_duration(self) -> None:
        params = Command.TimedSwitch(duration_seconds=-1.0)
        result = self.server.TimedSwitch(params)
        self.assertEqual(result.response, INVALID_ARGUMENTS)
        self.server.driver.on.assert_not_called()

    def test_estimate_timed_switch(self) -> None:
        params = Command.TimedSwitch(duration_seconds=3.7)
        result = self.server.EstimateTimedSwitch(params)
        self.assertEqual(result, math.ceil(3.7))


if __name__ == "__main__":
    unittest.main()
