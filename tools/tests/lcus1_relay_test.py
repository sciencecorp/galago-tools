import unittest
from unittest.mock import MagicMock, patch
import math

from tools.grpc_interfaces.lcus1_relay_pb2 import Command, Config
from tools.grpc_interfaces.tool_base_pb2 import INVALID_ARGUMENTS
from tools.lcus1_relay.server import Lcus1RelayServer


class TestTimedSwitch(unittest.TestCase):
    def setUp(self) -> None:
        from tools.grpc_interfaces.tool_base_pb2 import READY

        self.patcher_on = patch(
            "tools.lcus1_relay.driver.Lcus1RelayDriver.on", new_callable=MagicMock
        )
        self.patcher_off = patch(
            "tools.lcus1_relay.driver.Lcus1RelayDriver.off", new_callable=MagicMock
        )
        self.mock_on = self.patcher_on.start()
        self.mock_off = self.patcher_off.start()
        self.addCleanup(self.patcher_on.stop)
        self.addCleanup(self.patcher_off.stop)
        self.server = Lcus1RelayServer()
        self.server.driver = MagicMock()
        self.server.config = Config(com_port="COM4")
        self.server.simulated = False
        self.server.status = READY

    def test_timed_switch_rejects_zero_duration(self) -> None:
        params = Command.TimedSwitch(duration_seconds=0.0)
        result = self.server.TimedSwitch(params)
        if result is not None:
            self.assertEqual(result.response, INVALID_ARGUMENTS)
        self.mock_on.assert_not_called()

    def test_timed_switch_rejects_negative_duration(self) -> None:
        params = Command.TimedSwitch(duration_seconds=-1.0)
        result = self.server.TimedSwitch(params)
        if result is not None:
            self.assertEqual(result.response, INVALID_ARGUMENTS)
        self.mock_on.assert_not_called()

    def test_estimate_timed_switch(self) -> None:
        params = Command.TimedSwitch(duration_seconds=3.7)
        result = self.server.EstimateTimedSwitch(params)
        self.assertEqual(result, math.ceil(3.7))


if __name__ == "__main__":
    unittest.main()
