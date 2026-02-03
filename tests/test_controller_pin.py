
import pytest

from hondalink.config import settings
from hondalink.controller import AppNotReadyException, HondaLinkController
from hondalink.driver_mock import MockDriver


@pytest.fixture
def mock_driver():
    return MockDriver()

@pytest.fixture
def controller(mock_driver):
    return HondaLinkController(mock_driver)

def test_pin_entry_logic_success(controller, mock_driver):
    settings.pin_code = "1234"
    mock_driver.connect()

    # Setup state: "Enter PIN" exists, and an EditText exists
    mock_driver.register_element("text=Enter PIN", exists=True)
    pin_input = mock_driver.register_element("xpath=//android.widget.EditText", exists=True)
    ok_btn = mock_driver.register_element("text=OK", exists=True)

    # Initial call to ensure_app_open
    controller.ensure_app_open()

    assert pin_input.input_text == "1234"
    assert ok_btn.clicked

def test_pin_entry_logic_no_config(controller, mock_driver):
    settings.pin_code = None
    mock_driver.connect()

    mock_driver.register_element("text=Enter PIN", exists=True)

    with pytest.raises(AppNotReadyException):
        controller.ensure_app_open()

def test_hierarchy(controller, mock_driver):
    xml = controller.get_xml_hierarchy()
    assert xml == "<mock>hierarchy</mock>"
