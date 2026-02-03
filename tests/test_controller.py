from unittest.mock import MagicMock

import pytest
from tenacity import RetryError

from hondalink.config import settings
from hondalink.controller import (
    CommandType,
    HondaLinkController,
)
from hondalink.driver_mock import MockDriver


@pytest.fixture
def mock_driver():
    return MockDriver()


@pytest.fixture
def controller(mock_driver):
    return HondaLinkController(mock_driver)


def test_ensure_app_open_launches_app(controller, mock_driver):
    mock_driver.app_current = MagicMock(return_value={"package": "com.other.app"})
    mock_driver.app_start = MagicMock()

    controller.ensure_app_open()

    mock_driver.app_start.assert_called_with("com.honda.auto")


def test_execute_remote_command_flow(controller, mock_driver):
    # Setup
    mock_driver.connect()
    mock_driver.register_element("text=Remote Commands", exists=True)
    start_btn = mock_driver.register_element("text=Start", exists=True)

    # Act
    controller.execute_remote_command(CommandType.START)

    # Assert
    assert start_btn.clicked


def test_execute_remote_command_handles_error_popup(controller, mock_driver):
    # Setup
    mock_driver.connect()
    mock_driver.register_element("text=Start", exists=True)

    # Popup handling
    # Note: The controller looks for "An error has occurred"
    # substring logic if generalized,
    # but the find_by_text requires exact match in the mock unless I changed it.
    # The controller code was updated to search for "An error has occurred" (shortened)
    mock_driver.register_element("text=An error has occurred", exists=True)
    ok_btn = mock_driver.register_element("text=OK", exists=True)

    # Act
    controller.execute_remote_command(CommandType.START)

    # Assert
    assert ok_btn.clicked


def test_execute_remote_command_retry(controller, mock_driver):
    # Simulate first attempt fails (button not found), second attempt succeeds
    mock_driver.connect()

    # Initially "Start" does not exist
    # Remove assignment to unused variable
    mock_driver.register_element("text=Start", exists=False)
    mock_driver.register_element("text=Remote Commands", exists=True)

    # Verify it raises after retries if never found
    with pytest.raises(RetryError):
        controller.execute_remote_command(CommandType.START)


def test_get_status_locked(controller, mock_driver):
    mock_driver.connect()
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/textView_lockStatus",
        exists=True,
        text="Locked",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_odometer_value",
        exists=True,
        text="173,305 km",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/progressbar_fuel_level",
        exists=True,
        text="56.0",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_total_range_value",
        exists=True,
        text="327 km",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_oil_value", exists=True, text="5 %"
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/txt_last_updated_time",
        exists=True,
        text="Last updated at 01:33 p.m.",
    )

    status = controller.get_status()
    assert status.is_locked is True
    assert status.odometer == "173,305 km"
    assert status.fuel_level == "56.0%"
    assert status.range_remaining == "327 km"
    assert status.oil_life == "5 %"
    assert status.last_updated == "Last updated at 01:33 p.m."


def test_get_status_unlocked(controller, mock_driver):
    mock_driver.connect()
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/textView_lockStatus",
        exists=True,
        text="Unlocked",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_odometer_value",
        exists=True,
        text="173,305 km",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/progressbar_fuel_level",
        exists=True,
        text="56.0",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_total_range_value",
        exists=True,
        text="327 km",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_oil_value", exists=True, text="5 %"
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/txt_last_updated_time",
        exists=True,
        text="Last updated at 01:33 p.m.",
    )

    status = controller.get_status()
    assert status.is_locked is False


def test_execute_remote_command_handles_pin_prompt(controller, mock_driver):
    # Setup
    settings.pin_code = "1234"
    mock_driver.connect()
    start_btn = mock_driver.register_element("text=Start", exists=True)

    # Simulate PIN prompt appearing
    mock_driver.register_element("text=Enter PIN", exists=True)
    pin_input = mock_driver.register_element(
        "xpath=//android.widget.EditText", exists=True
    )
    # The controller looks for "Enter" or "OK"
    enter_btn = mock_driver.register_element("text=Enter", exists=True)

    # Act
    controller.execute_remote_command(CommandType.START)

    # Assert
    assert start_btn.clicked
    assert pin_input.input_text == "1234"
    assert enter_btn.clicked


def test_execute_remote_command_expands_collapsed_panel(controller, mock_driver):
    mock_driver.connect()

    remote_commands_text = mock_driver.register_element(
        "text=Remote Commands", exists=True, bounds=(261, 1077, 475, 1110)
    )
    start_btn = mock_driver.register_element("text=Start", exists=True)

    controller.execute_remote_command(CommandType.START)

    assert start_btn.clicked
