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

    controller.ensure_app_open()

    assert pin_field1.input_text == "1"
    assert pin_field2.input_text == "2"
    assert pin_field3.input_text == "3"
    assert pin_field4.input_text == "4"
    assert pin_field1.clicked
    assert pin_field2.clicked
    assert pin_field3.clicked
    assert pin_field4.clicked


def test_pin_entry_logic_no_config(controller, mock_driver):
    settings.pin_code = None
    mock_driver.connect()

    mock_driver.register_element(
        "id=com.honda.hondalink.connect:id/pinView", exists=True
    )

    with pytest.raises(AppNotReadyException):
        controller.ensure_app_open()


def test_hierarchy(controller, mock_driver):
    xml = controller.get_xml_hierarchy()
    assert xml == "<mock>hierarchy</mock>"
