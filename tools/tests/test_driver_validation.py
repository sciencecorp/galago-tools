"""
Unit tests for driver input validation and argument transformation.

These tests focus on high-value cases:
- Input validation (catches bugs before they hit hardware)
- Argument transformation (enum mappings, type conversions)
- Public API stability (method signatures haven't changed)

Note: These tests mock COM objects since actual hardware isn't available.
They verify driver logic, not hardware interaction.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Any, Generator
import sys

# Mock Windows-specific modules before importing drivers
sys.modules['pythoncom'] = MagicMock()
sys.modules['clr'] = MagicMock()
sys.modules['System'] = MagicMock()
sys.modules['System.Windows'] = MagicMock()
sys.modules['System.Windows.Forms'] = MagicMock()
sys.modules['System.Drawing'] = MagicMock()

# Mock Windows DLL modules that drivers import on Windows
sys.modules['AxCentrifugeLib'] = MagicMock()
sys.modules['AxCentrifugeLoaderLib'] = MagicMock()
sys.modules['AxBenchCelLib'] = MagicMock()
sys.modules['AxMiniHubLib'] = MagicMock()
sys.modules['AxStackerLib'] = MagicMock()

# Import drivers after mocking - this ensures modules are loaded
# before we try to patch them
from tools.vspin.driver import VSpin  # noqa: E402
from tools.vspin_with_loader.driver import VSpinWithLoader, LoadSpeed  # noqa: E402
from tools.benchcel.driver import BenchCelDriver  # noqa: E402
from tools.minihub.driver import MiniHubDriver  # noqa: E402
from tools.vstack.driver import VStackDriver  # noqa: E402


class TestVSpinValidation:
    """Tests for VSpin driver input validation."""

    @pytest.fixture
    def mock_vspin(self) -> Generator[Any, None, None]:
        """Create a VSpin instance with mocked COM objects."""
        with patch.object(VSpin, 'instantiate'):
            driver = VSpin(profile="test_profile")
            driver.client = MagicMock()
            with patch.object(driver, 'schedule_threaded_command'):
                yield driver

    def test_spin_valid_time_minimum(self, mock_vspin: Any) -> None:
        """Time just above minimum (1) should be accepted."""
        mock_vspin.spin(time=2, velocity_percent=50, acceleration_percent=50,
                       decel_percent=50, timer_mode=0, bucket=1)
        mock_vspin.schedule_threaded_command.assert_called_once()

    def test_spin_valid_time_maximum(self, mock_vspin: Any) -> None:
        """Time just below maximum (86400) should be accepted."""
        mock_vspin.spin(time=86399, velocity_percent=50, acceleration_percent=50,
                       decel_percent=50, timer_mode=0, bucket=1)
        mock_vspin.schedule_threaded_command.assert_called_once()

    def test_spin_invalid_time_zero(self, mock_vspin: Any) -> None:
        """Time of 0 should raise ValueError."""
        with pytest.raises(ValueError, match="Time must be between 1 and 86400"):
            mock_vspin.spin(time=0, velocity_percent=50, acceleration_percent=50,
                          decel_percent=50, timer_mode=0, bucket=1)

    def test_spin_invalid_time_one(self, mock_vspin: Any) -> None:
        """Time of exactly 1 should raise ValueError (must be > 1)."""
        with pytest.raises(ValueError, match="Time must be between 1 and 86400"):
            mock_vspin.spin(time=1, velocity_percent=50, acceleration_percent=50,
                          decel_percent=50, timer_mode=0, bucket=1)

    def test_spin_invalid_time_too_large(self, mock_vspin: Any) -> None:
        """Time >= 86400 should raise ValueError."""
        with pytest.raises(ValueError, match="Time must be between 1 and 86400"):
            mock_vspin.spin(time=86400, velocity_percent=50, acceleration_percent=50,
                          decel_percent=50, timer_mode=0, bucket=1)

    def test_spin_invalid_time_negative(self, mock_vspin: Any) -> None:
        """Negative time should raise ValueError."""
        with pytest.raises(ValueError, match="Time must be between 1 and 86400"):
            mock_vspin.spin(time=-100, velocity_percent=50, acceleration_percent=50,
                          decel_percent=50, timer_mode=0, bucket=1)

    def test_spin_arguments_passed_correctly(self, mock_vspin: Any) -> None:
        """Verify spin passes correct arguments to schedule_threaded_command."""
        mock_vspin.spin(time=100, velocity_percent=75, acceleration_percent=80,
                       decel_percent=60, timer_mode=1, bucket=2)

        call_args = mock_vspin.schedule_threaded_command.call_args
        assert call_args[0][0] == "spin"
        args = call_args[0][1]
        assert args["time"] == 100
        assert args["velocity_percent"] == 75
        assert args["acceleration_percent"] == 80
        assert args["deceleration_percent"] == 60
        assert args["timer_mode"] == 1
        assert args["bucket_number"] == 2


class TestVSpinWithLoaderValidation:
    """Tests for VSpinWithLoader driver input validation and transformations."""

    @pytest.fixture
    def mock_vspin_loader(self) -> Generator[Any, None, None]:
        """Create a VSpinWithLoader instance with mocked COM objects."""
        with patch.object(VSpinWithLoader, 'instantiate'):
            driver = VSpinWithLoader(profile="test_profile")
            driver.client = MagicMock()
            with patch.object(driver, 'schedule_threaded_command'):
                yield driver

    def test_spin_valid_time(self, mock_vspin_loader: Any) -> None:
        """Valid time should be accepted."""
        mock_vspin_loader.spin(time=100, velocity_percent=50, acceleration_percent=50,
                              decel_percent=50, timer_mode=0, bucket=1)
        mock_vspin_loader.schedule_threaded_command.assert_called_once()

    def test_spin_invalid_time_too_small(self, mock_vspin_loader: Any) -> None:
        """Time <= 1 should raise ValueError."""
        with pytest.raises(ValueError, match="Time must be between 1 and 86400"):
            mock_vspin_loader.spin(time=1, velocity_percent=50, acceleration_percent=50,
                                  decel_percent=50, timer_mode=0, bucket=1)

    def test_spin_invalid_time_too_large(self, mock_vspin_loader: Any) -> None:
        """Time >= 86400 should raise ValueError."""
        with pytest.raises(ValueError, match="Time must be between 1 and 86400"):
            mock_vspin_loader.spin(time=86400, velocity_percent=50, acceleration_percent=50,
                                  decel_percent=50, timer_mode=0, bucket=1)


class TestLoadSpeedEnum:
    """Tests for LoadSpeed enum transformation."""

    def test_load_speed_values(self) -> None:
        """Verify LoadSpeed enum has correct values."""
        assert LoadSpeed.SLOW.value == 1
        assert LoadSpeed.MEDIUM.value == 2
        assert LoadSpeed.FAST.value == 3

    def test_load_speed_case_insensitive_lookup(self) -> None:
        """Verify enum lookup works with different cases."""
        # This is how the driver uses it: LoadSpeed[speed.upper()]
        assert LoadSpeed["SLOW"].value == 1
        assert LoadSpeed["MEDIUM"].value == 2
        assert LoadSpeed["FAST"].value == 3

    def test_load_speed_invalid_raises_keyerror(self) -> None:
        """Invalid speed string should raise KeyError."""
        with pytest.raises(KeyError):
            LoadSpeed["INVALID"]

        with pytest.raises(KeyError):
            LoadSpeed["slow"]  # lowercase doesn't work directly


class TestLoadPlateArgumentTransformation:
    """Tests for load_plate/unload_plate argument transformation."""

    @pytest.fixture
    def mock_vspin_loader(self) -> Generator[Any, None, None]:
        """Create a VSpinWithLoader instance with mocked COM objects."""
        with patch.object(VSpinWithLoader, 'instantiate'):
            driver = VSpinWithLoader(profile="test_profile")
            driver.client = MagicMock()
            with patch.object(driver, 'schedule_threaded_command'):
                yield driver

    def test_load_plate_speed_slow(self, mock_vspin_loader: Any) -> None:
        """Speed 'slow' should be converted to enum value 1."""
        mock_vspin_loader.load_plate(bucket_number=1, gripper_offset=5.0,
                                     plate_height=10.0, speed="slow", options=0)

        call_args = mock_vspin_loader.schedule_threaded_command.call_args
        assert call_args[0][1]["speed"] == 1  # LoadSpeed.SLOW.value

    def test_load_plate_speed_medium(self, mock_vspin_loader: Any) -> None:
        """Speed 'medium' should be converted to enum value 2."""
        mock_vspin_loader.load_plate(bucket_number=1, gripper_offset=5.0,
                                     plate_height=10.0, speed="medium", options=0)

        call_args = mock_vspin_loader.schedule_threaded_command.call_args
        assert call_args[0][1]["speed"] == 2  # LoadSpeed.MEDIUM.value

    def test_load_plate_speed_fast(self, mock_vspin_loader: Any) -> None:
        """Speed 'fast' should be converted to enum value 3."""
        mock_vspin_loader.load_plate(bucket_number=1, gripper_offset=5.0,
                                     plate_height=10.0, speed="FAST", options=0)

        call_args = mock_vspin_loader.schedule_threaded_command.call_args
        assert call_args[0][1]["speed"] == 3  # LoadSpeed.FAST.value

    def test_load_plate_speed_case_insensitive(self, mock_vspin_loader: Any) -> None:
        """Speed should be case-insensitive (converted via .upper())."""
        mock_vspin_loader.load_plate(bucket_number=1, gripper_offset=5.0,
                                     plate_height=10.0, speed="MeDiUm", options=0)

        call_args = mock_vspin_loader.schedule_threaded_command.call_args
        assert call_args[0][1]["speed"] == 2  # LoadSpeed.MEDIUM.value

    def test_load_plate_invalid_speed(self, mock_vspin_loader: Any) -> None:
        """Invalid speed string should raise KeyError."""
        with pytest.raises(KeyError):
            mock_vspin_loader.load_plate(bucket_number=1, gripper_offset=5.0,
                                        plate_height=10.0, speed="turbo", options=0)

    def test_unload_plate_speed_transformation(self, mock_vspin_loader: Any) -> None:
        """Unload plate should also transform speed correctly."""
        mock_vspin_loader.unload_plate(bucket_number=1, gripper_offset=5.0,
                                       plate_height=10.0, speed="fast", options=0)

        call_args = mock_vspin_loader.schedule_threaded_command.call_args
        assert call_args[0][1]["speed"] == 3  # LoadSpeed.FAST.value


class TestDriverPublicAPI:
    """Tests to verify driver public APIs haven't changed unexpectedly."""

    def test_vspin_has_expected_methods(self) -> None:
        """VSpin should have all expected public methods."""
        expected_methods = [
            'initialize', 'close', 'show_diagnostics', 'home',
            'close_door', 'open_door', 'spin', 'stop_spin',
            'schedule_threaded_command', 'execute_command', 'instantiate'
        ]

        for method in expected_methods:
            assert hasattr(VSpin, method), f"VSpin missing method: {method}"

    def test_vspin_with_loader_has_expected_methods(self) -> None:
        """VSpinWithLoader should have all expected public methods."""
        expected_methods = [
            'initialize', 'close', 'show_diagnostics', 'home',
            'close_door', 'open_door', 'spin', 'stop_spin',
            'load_plate', 'unload_plate', 'park',
            'schedule_threaded_command', 'execute_command', 'instantiate'
        ]

        for method in expected_methods:
            assert hasattr(VSpinWithLoader, method), f"VSpinWithLoader missing method: {method}"

    def test_benchcel_has_expected_methods(self) -> None:
        """BenchCelDriver should have all expected public methods."""
        expected_methods = [
            'initialize', 'close', 'pick_and_place', 'delid', 'relid',
            'load_stack', 'release_stack', 'open_clamp', 'is_stack_loaded',
            'is_plate_present', 'set_labware', 'get_stack_count',
            'get_teachpoint_names', 'get_labware_names', 'protocol_start',
            'protocol_finish', 'move_to_home_position', 'pause', 'unpause',
            'show_diagnostics', 'show_labware_editor',
            'schedule_threaded_command', 'execute_command'
        ]

        for method in expected_methods:
            assert hasattr(BenchCelDriver, method), f"BenchCelDriver missing method: {method}"

    def test_minihub_has_expected_methods(self) -> None:
        """MiniHubDriver should have all expected public methods."""
        expected_methods = [
            'initialize', 'close', 'abort', 'disable_motor', 'enable_motor',
            'jog', 'rotate_to_cassette', 'rotate_to_degree',
            'rotate_to_home_position', 'set_speed', 'show_diagnostics', 'teach_home',
            'schedule_threaded_command', 'execute_command'
        ]

        for method in expected_methods:
            assert hasattr(MiniHubDriver, method), f"MiniHubDriver missing method: {method}"

    def test_vstack_has_expected_methods(self) -> None:
        """VStackDriver should have all expected public methods."""
        expected_methods = [
            'initialize', 'close', 'abort', 'downstack', 'home', 'jog',
            'load_stack', 'open_gripper', 'release_stack', 'set_button_mode',
            'set_labware', 'show_diagnostics', 'upstack',
            'schedule_threaded_command', 'execute_command'
        ]

        for method in expected_methods:
            assert hasattr(VStackDriver, method), f"VStackDriver missing method: {method}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
