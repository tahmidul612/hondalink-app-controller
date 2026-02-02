import pytest
from unittest.mock import MagicMock
from hondalink.controller import HondaLinkController, CommandFailedException, CommandType
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
    mock_driver.register_element("text=An error has occurred. Please try again later", exists=True)
    ok_btn = mock_driver.register_element("text=OK", exists=True)

    # Act
    controller.execute_remote_command(CommandType.START)

    # Assert
    assert ok_btn.clicked

def test_execute_remote_command_retry(controller, mock_driver):
    # Simulate first attempt fails (button not found), second attempt succeeds
    mock_driver.connect()

    # Initially "Start" does not exist
    start_btn = mock_driver.register_element("text=Start", exists=False)
    mock_driver.register_element("text=Remote Commands", exists=True)

    # We can't easily change the mock state *during* the call with the current mock implementation.
    # The MockDriver is simple.
    # However, tenacity retries.
    # If the button is missing, it raises CommandFailedException.

    # Let's verify it raises after retries if never found
    from tenacity import RetryError
    with pytest.raises(RetryError):
        controller.execute_remote_command(CommandType.START)

def test_get_status_locked(controller, mock_driver):
    mock_driver.connect()
    mock_driver.register_element("text=Locked", exists=True)

    status = controller.get_status()
    assert status.is_locked is True

def test_get_status_unlocked(controller, mock_driver):
    mock_driver.connect()
    mock_driver.register_element("text=Locked", exists=False)

    status = controller.get_status()
    assert status.is_locked is False
