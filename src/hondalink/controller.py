import logging
import time

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from .config import settings
from .driver import AndroidDriver
from .models import CommandType, VehicleStatus

logger = logging.getLogger(__name__)

class HondaLinkException(Exception):
    pass

class AppNotReadyException(HondaLinkException):
    pass

class CommandFailedException(HondaLinkException):
    pass

class HondaLinkController:
    def __init__(self, driver: AndroidDriver):
        self.driver = driver
        self.package = settings.hondalink_package

    def connect(self):
        """Connects to the device."""
        logger.info(f"Connecting to device at {settings.android_device_ip or 'USB'}")
        self.driver.connect(settings.android_device_ip)

    def get_xml_hierarchy(self) -> str:
        """Returns the current UI hierarchy as XML."""
        return self.driver.dump_hierarchy()

    def _handle_pin_entry(self) -> bool:
        """
        Checks for PIN entry screen and enters PIN if present.
        Returns True if PIN was entered, False otherwise.
        """
        pin_label = self.driver.find_by_text("Enter PIN")
        if pin_label.exists():
            logger.info("PIN screen detected")
            if settings.pin_code:
                # Try to find an input field
                # Using generic XPath for EditText
                pin_input = self.driver.find_by_xpath("//android.widget.EditText")
                if pin_input.exists():
                    pin_input.set_text(settings.pin_code)
                    # Look for Enter or OK button
                    ok_btn = self.driver.find_by_text("Enter")
                    if not ok_btn.exists():
                        ok_btn = self.driver.find_by_text("OK")

                    if ok_btn.exists():
                        ok_btn.click()
                        time.sleep(3)
                        return True
                else:
                    logger.warning("PIN label found but no input field found")
            else:
                logger.error("PIN required but not configured in settings")
                raise AppNotReadyException("PIN required but not configured")
        return False

    def ensure_app_open(self):
        """Ensures the app is in the foreground and ready."""
        current = self.driver.app_current()
        if current.get("package") != self.package:
            logger.info("Starting HondaLink app...")
            self.driver.app_start(self.package)
            time.sleep(5)  # Wait for launch

        # Check for PIN screen (initial launch)
        self._handle_pin_entry()

        # Check for unexpected popups (e.g. "Agree" to terms)
        self._handle_popups()

    def _handle_popups(self):
        """Dismisses common popups."""
        # Example: "An error has occurred" -> OK
        error_popup = self.driver.find_by_text("An error has occurred")
        if error_popup.exists():
            logger.warning("Found error popup, dismissing.")
            ok_btn = self.driver.find_by_text("OK")
            if ok_btn.exists():
                ok_btn.click()
                time.sleep(1)

    def _navigate_to_home(self):
        """Navigates to the main dashboard screen."""
        pass

        # If we see "Refresh" button, we are likely on a good screen.
        if not self.driver.find_by_text("Refresh").exists():
            # Try pressing back?
            # self.driver.press("back")
            pass

    def get_status(self) -> VehicleStatus:
        self.ensure_app_open()
        self._navigate_to_home()

        # Refresh data?
        refresh_btn = self.driver.find_by_text("Refresh")
        if refresh_btn.exists():
            refresh_btn.click()
            time.sleep(2) # Wait for refresh?

        # Parse data
        odometer = "Unknown"
        fuel = "Unknown"
        range_val = "Unknown"
        oil = "Unknown"
        locked = False
        last_updated = "Unknown"

        if self.driver.find_by_text("Locked").exists():
            locked = True

        return VehicleStatus(
            odometer=odometer,
            fuel_level=fuel,
            range_remaining=range_val,
            oil_life=oil,
            is_locked=locked,
            last_updated=last_updated
        )

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(CommandFailedException)
    )
    def execute_remote_command(self, command: CommandType):
        self.ensure_app_open()
        self._handle_popups()

        # Open Remote Commands if not visible
        if not self.driver.find_by_text("Start").exists():
            remote_cmd_btn = self.driver.find_by_text("Remote Commands")
            if remote_cmd_btn.exists():
                remote_cmd_btn.click()
                time.sleep(2)

        if not self.driver.find_by_text("Start").exists():
            raise CommandFailedException("Could not open Remote Commands menu")

        btn_text = {
            CommandType.START: "Start",
            CommandType.STOP: "Stop",
            CommandType.LOCK: "Lock",
            CommandType.UNLOCK: "Unlock"
        }.get(command)

        if not btn_text:
            raise CommandFailedException(f"Unknown command {command}")

        btn = self.driver.find_by_text(btn_text)
        if not btn.exists():
             raise CommandFailedException(f"Button {btn_text} not found")

        logger.info(f"Clicking command button: {btn_text}")
        btn.click()

        # Poll for PIN screen or result
        # The user noted: "it takes a second or two for the screen to appear... continuously be checking"
        logger.info("Waiting for PIN screen or result...")
        start_time = time.time()
        pin_entered = False

        while time.time() - start_time < 10:
            if self._handle_pin_entry():
                pin_entered = True
                logger.info("PIN entered successfully.")
                break

            # Also check for popups here just in case
            self._handle_popups()

            time.sleep(0.5)

        if pin_entered:
            # Wait a bit more for the command to actually process after PIN
            time.sleep(5)

        logger.info(f"Command {command} executed")
        return True
