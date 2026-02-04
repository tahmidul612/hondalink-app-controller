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

    mock_driver.app_start.assert_called_with("com.honda.hondalink.connect", stop=True)


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
    mock_driver.connect()
    mock_driver.register_element("text=Start", exists=True)

    mock_driver.register_element(
        "id=android:id/message", exists=True, text="An error has occurred"
    )
    ok_btn = mock_driver.register_element("text=OK", exists=True)

    controller.execute_remote_command(CommandType.START)

    assert ok_btn.clicked


def test_execute_remote_command_handles_something_went_wrong_popup(
    controller, mock_driver
):
    mock_driver.connect()
    mock_driver.register_element("text=Start", exists=True)

    mock_driver.register_element(
        "id=android:id/message",
        exists=True,
        text="Something went wrong with your request",
    )
    ok_btn = mock_driver.register_element("text=OK", exists=True)

    controller.execute_remote_command(CommandType.START)

    assert ok_btn.clicked


def test_execute_remote_command_handles_generic_error_popup(controller, mock_driver):
    mock_driver.connect()
    mock_driver.register_element("text=Start", exists=True)

    mock_driver.register_element(
        "id=android:id/message", exists=True, text="Connection error occurred"
    )
    ok_btn = mock_driver.register_element("text=OK", exists=True)

    controller.execute_remote_command(CommandType.START)

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
    settings.pin_code = "1234"
    mock_driver.connect()
    start_btn = mock_driver.register_element("text=Start", exists=True)

    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/pinView", exists=True
    )
    pin_field1 = mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/pinText_one", exists=True
    )
    pin_field2 = mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/pinText_two", exists=True
    )
    pin_field3 = mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/pinText_three", exists=True
    )
    pin_field4 = mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/pinText_four", exists=True
    )
    mock_driver.register_element("text=Incorrect PIN", exists=False)

    controller.execute_remote_command(CommandType.START)

    assert start_btn.clicked
    assert pin_field1.input_text == "1"
    assert pin_field2.input_text == "2"
    assert pin_field3.input_text == "3"
    assert pin_field4.input_text == "4"


def test_execute_remote_command_expands_collapsed_panel(controller, mock_driver):
    mock_driver.connect()

    mock_driver.register_element(
        "text=Remote Commands", exists=True, bounds=(261, 1077, 475, 1110)
    )
    start_btn = mock_driver.register_element("text=Start", exists=True)

    controller.execute_remote_command(CommandType.START)

    assert start_btn.clicked


def test_get_status_caches_successful_result(controller, mock_driver):
    mock_driver.connect()
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/textView_lockStatus",
        exists=True,
        text="Locked",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_odometer_value",
        exists=True,
        text="100,000 km",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/progressbar_fuel_level",
        exists=True,
        text="75.0",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_total_range_value",
        exists=True,
        text="400 km",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_oil_value", exists=True, text="50 %"
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/txt_last_updated_time",
        exists=True,
        text="Last updated at 01:00 p.m.",
    )

    assert controller.last_known_status is None

    controller.get_status()

    assert controller.last_known_status is not None
    assert controller.last_known_status.odometer == "100,000 km"
    assert controller.last_known_status.fuel_level == "75.0%"


def test_get_status_returns_cached_when_live_fails(controller, mock_driver):
    mock_driver.connect()
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/textView_lockStatus",
        exists=True,
        text="Locked",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_odometer_value",
        exists=True,
        text="100,000 km",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/progressbar_fuel_level",
        exists=True,
        text="75.0",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_total_range_value",
        exists=True,
        text="400 km",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_oil_value", exists=True, text="50 %"
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/txt_last_updated_time",
        exists=True,
        text="Last updated at 01:00 p.m.",
    )

    first_status = controller.get_status()
    assert first_status.odometer == "100,000 km"

    mock_driver.app_current = MagicMock(side_effect=Exception("Connection lost"))

    second_status = controller.get_status()

    assert second_status.odometer == "100,000 km"
    assert second_status.fuel_level == "75.0%"


def test_get_status_returns_cached_when_all_unknown(controller, mock_driver):
    mock_driver.connect()
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/textView_lockStatus",
        exists=True,
        text="Locked",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_odometer_value",
        exists=True,
        text="100,000 km",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/progressbar_fuel_level",
        exists=True,
        text="75.0",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_total_range_value",
        exists=True,
        text="400 km",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_oil_value", exists=True, text="50 %"
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/txt_last_updated_time",
        exists=True,
        text="Last updated at 01:00 p.m.",
    )

    first_status = controller.get_status()
    assert first_status.odometer == "100,000 km"

    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_odometer_value",
        exists=False,
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/progressbar_fuel_level",
        exists=False,
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_total_range_value",
        exists=False,
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/tv_oil_value", exists=False
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/txt_last_updated_time",
        exists=False,
    )

    second_status = controller.get_status()

    assert second_status.odometer == "100,000 km"
    assert second_status.fuel_level == "75.0%"


def test_get_status_raises_when_no_cache_and_exception(controller, mock_driver):
    mock_driver.connect()

    mock_driver.app_current = MagicMock(side_effect=Exception("Connection lost"))

    with pytest.raises(Exception, match="Connection lost"):
        controller.get_status()


def test_get_remote_start_status_active(controller, mock_driver):
    mock_driver.connect()
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/text_success_timer",
        exists=True,
        text="09:58",
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/remote_command_inside_temp",
        exists=True,
        text="-2 °C",
    )

    status = controller.get_remote_start_status()
    assert status.is_active is True
    assert status.remaining_time == "09:58"
    assert status.cabin_temperature == "-2 °C"


def test_get_remote_start_status_inactive(controller, mock_driver):
    mock_driver.connect()
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/text_success_timer",
        exists=False,
    )
    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/remote_command_inside_temp",
        exists=False,
    )

    status = controller.get_remote_start_status()
    assert status.is_active is False
    assert status.remaining_time == "Unknown"
    assert status.cabin_temperature == "Unknown"


def test_execute_remote_command_uses_extend_when_active(controller, mock_driver):
    mock_driver.connect()
    extend_btn = mock_driver.register_element("text=Extend", exists=True)
    mock_driver.register_element("text=Start", exists=True)

    controller.execute_remote_command(CommandType.START)

    assert extend_btn.clicked
