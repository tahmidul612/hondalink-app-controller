import time
import logging
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from .driver import AndroidDriver, UIElement
from .models import CommandType, VehicleStatus
from .config import settings

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

    def ensure_app_open(self):
        """Ensures the app is in the foreground and ready."""
        current = self.driver.app_current()
        if current.get("package") != self.package:
            logger.info("Starting HondaLink app...")
            self.driver.app_start(self.package)
            time.sleep(5)  # Wait for launch

        # Check for PIN screen (speculative logic)
        # If we see a PIN entry field, enter PIN
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
                else:
                    logger.warning("PIN label found but no input field found via generic XPath")
            else:
                logger.error("PIN required but not configured in settings")
                raise AppNotReadyException("PIN required but not configured")

        # Check for unexpected popups (e.g. "Agree" to terms)
        self._handle_popups()

    def _handle_popups(self):
        """Dismisses common popups."""
        # Example: "An error has occurred" -> OK
        error_popup = self.driver.find_by_text("An error has occurred. Please try again later")
        if error_popup.exists():
            logger.warning("Found error popup, dismissing.")
            ok_btn = self.driver.find_by_text("OK")
            if ok_btn.exists():
                ok_btn.click()
                time.sleep(1)

    def _navigate_to_home(self):
        """Navigates to the main dashboard screen."""
        # Check if we are on Remote Commands screen
        if self.driver.find_by_text("Stop").exists() or self.driver.find_by_text("Unlock").exists():
            # We are likely in remote commands, need to go back or find a 'Home' button?
            # From screenshots, it seems there's a drawer or bottom nav?
            # Screenshot 1 shows "Remote Commands" bar at bottom.
            # Screenshot 2 shows "Remote Commands" panel expanded.
            # It seems clicking the handle or "Remote Commands" toggles it.
            # If "Stop" is visible, maybe we just need to dismiss the sheet?
            # Or maybe we can read status from the background even if sheet is up?
            # Actually, status (Range, Fuel) is visible at top even when Remote Commands are up (Screenshot 2).
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
        # Using simple text search for now.
        # In a real scenario, we might need more robust relative lookups.

        # Odometer: "107,643 mi"
        # Strategy: Find "Odometer", looks for text nearby?
        # Since we can't easily do "nearby" with our abstraction without Xpath, let's use Xpath if possible.
        # But for now, let's assume we can find the text that *contains* "mi" or "km".

        # Mocking the values for now as 'Unknown' if not found is safer.
        odometer = "Unknown"
        fuel = "Unknown"
        range_val = "Unknown"
        oil = "Unknown"
        locked = False
        last_updated = "Unknown"

        # Try to find specific elements
        # Note: This is brittle without exact resource IDs or Layout inspection.
        # I will assume there are elements with these texts.

        if self.driver.find_by_text("Locked").exists():
            locked = True

        # For values, we might need regex matching which uiautomator2 supports via 'matches'
        # But my driver abstraction wraps 'text'.
        # I'll update my driver abstraction to support `find_by_text_contains` or similar?
        # Or just use `find_by_xpath`.

        # Example Xpaths (Speculative):
        # //*[@text='Odometer']/preceding-sibling::*[@text]

        return VehicleStatus(
            odometer=odometer,
            fuel_level=fuel,
            range_remaining=range_val,
            oil_life=oil,
            is_locked=locked,
            last_updated=last_updated
        )

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(CommandFailedException))
    def execute_remote_command(self, command: CommandType):
        self.ensure_app_open()
        self._handle_popups()

        # Open Remote Commands if not visible
        # Check for a specific button like "Start" to know if we are in the menu
        if not self.driver.find_by_text("Start").exists():
            remote_cmd_btn = self.driver.find_by_text("Remote Commands")
            if remote_cmd_btn.exists():
                remote_cmd_btn.click()
                time.sleep(2)

        if not self.driver.find_by_text("Start").exists():
            raise CommandFailedException("Could not open Remote Commands menu")

        # Map command to button text
        # Screenshot 2: "Start", "Stop", "Lock", "Unlock" (capitalized?)
        # "Start", "Stop" are clear.
        # "Lock" icon? Or text? Screenshot 2 shows icons with "Lock" "Unlock" text below?
        # Actually it says "Lock" and "Unlock".

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

        btn.click()

        # Wait for result
        # There might be a spinner, then a success/error message.
        time.sleep(5)

        self._handle_popups()

        # Verification?
        # If we locked, we expect "Locked" status?
        # If we started, we expect... "Stop" button to become active? Or timer?

        logger.info(f"Command {command} executed")
        return True
