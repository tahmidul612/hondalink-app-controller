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
        self.last_known_status: VehicleStatus | None = None

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
        # Fast check using more specific resource ID
        pin_view = self.driver.find_by_resource_id(
            "com.honda.hondalink.connect:id/pinView"
        )
        if not pin_view.exists():
            return False

        logger.info("PIN screen detected")
        if not settings.pin_code:
            logger.error("PIN required but not configured in settings")
            raise AppNotReadyException("PIN required but not configured")

        # Validate PIN is 4 digits
        pin = settings.pin_code.strip()
        if len(pin) != 4 or not pin.isdigit():
            logger.error(f"PIN must be exactly 4 digits, got: {len(pin)} characters")
            raise AppNotReadyException("PIN must be exactly 4 digits")

        # Enter each digit into its respective field using resource IDs
        pin_field_ids = [
            "com.honda.hondalink.connect:id/pinText_one",
            "com.honda.hondalink.connect:id/pinText_two",
            "com.honda.hondalink.connect:id/pinText_three",
            "com.honda.hondalink.connect:id/pinText_four",
        ]

        for i, field_id in enumerate(pin_field_ids):
            pin_field = self.driver.find_by_resource_id(field_id)
            if not pin_field.wait(timeout=5.0):
                logger.error(f"PIN field {i + 1} not found: {field_id}")
                raise AppNotReadyException(f"PIN field {i + 1} not found")

            # Click to focus and enter digit
            pin_field.click()
            time.sleep(0.05)  # Brief delay for focus
            pin_field.set_text(pin[i])

        logger.info("PIN entered successfully")
        # PIN is auto-submitted when 4th digit is entered, no need to click OK
        # Wait briefly for validation
        time.sleep(0.5)

        # Check for incorrect PIN error
        incorrect_pin = self.driver.find_by_text("Incorrect PIN")
        if incorrect_pin.exists():
            logger.error("Incorrect PIN entered")
            raise AppNotReadyException("Incorrect PIN")

        return True

    def ensure_app_open(self):
        """Ensures the app is in the foreground and ready."""
        current = self.driver.app_current()
        if current.get("package") != self.package:
            logger.info("Starting HondaLink app...")
            self.driver.app_start(self.package, stop=True)

            for _ in range(20):
                time.sleep(0.5)
                current = self.driver.app_current()
                if current.get("package") == self.package:
                    logger.info("App started successfully")
                    break
            else:
                logger.warning("App may not have started correctly")

        self._handle_pin_entry()
        self._handle_popups()

    def _handle_popups(self):
        """Dismisses common popups."""
        # Handle specific known error popups first
        error_popup = self.driver.find_by_text("An error has occurred")
        if error_popup.exists():
            logger.warning("Found 'An error has occurred' popup, dismissing.")
            ok_btn = self.driver.find_by_text("OK")
            if ok_btn.exists():
                ok_btn.click()
                time.sleep(1)
            return

        something_wrong_popup = self.driver.find_by_text("Something Went Wrong")
        if something_wrong_popup.exists():
            logger.warning("Found 'Something Went Wrong' popup, dismissing.")
            ok_btn = self.driver.find_by_text("OK")
            if ok_btn.exists():
                ok_btn.click()
                time.sleep(1)
            return

        # Generic error handler: catch any modal with "error" in text (case-insensitive)
        # XPath: find any element containing "error" or "Error" in its text
        generic_error = self.driver.find_by_xpath(
            "//*[contains(translate(@text, 'ERROR', 'error'), 'error')]"
        )
        if generic_error.exists():
            error_text = generic_error.text
            logger.warning(
                f"Found generic error popup with text: '{error_text}', dismissing."
            )
            ok_btn = self.driver.find_by_text("OK")
            if ok_btn.exists():
                ok_btn.click()
                time.sleep(1)
            return

        # Handle incorrect PIN separately as it should raise an exception
        incorrect_pin = self.driver.find_by_text("Incorrect PIN")
        if incorrect_pin.exists():
            logger.error("Incorrect PIN error popup detected")
            ok_btn = self.driver.find_by_text("OK")
            if ok_btn.exists():
                ok_btn.click()
                time.sleep(0.5)
            raise AppNotReadyException("Incorrect PIN entered")

    def _navigate_to_home(self):
        """Navigates to the main dashboard screen."""
        pass

        # If we see "Refresh" button, we are likely on a good screen.
        if not self.driver.find_by_text("Refresh").exists():
            # Try pressing back?
            # self.driver.press("back")
            pass

    def _expand_remote_commands_panel(self) -> bool:
        """
        Expands the Remote Commands bottom drawer panel if collapsed.
        Returns True if panel was successfully expanded or was already expanded.
        """
        if self.driver.find_by_text("Start").exists():
            logger.debug("Remote Commands panel already expanded")
            return True

        remote_commands_text = self.driver.find_by_text("Remote Commands")
        if not remote_commands_text.exists():
            logger.warning("Remote Commands panel not found")
            return False

        left, top, right, bottom = remote_commands_text.bounds()
        center_x = (left + right) // 2
        start_y = (top + bottom) // 2
        end_y = start_y - 200

        logger.info(
            f"Expanding Remote Commands panel by dragging from "
            f"({center_x}, {start_y}) to ({center_x}, {end_y})"
        )
        self.driver.swipe(center_x, start_y, center_x, end_y, duration=0.2)
        time.sleep(0.5)

        if self.driver.find_by_text("Start").exists():
            logger.info("Panel expanded successfully")
            return True

        logger.warning("Panel may still be collapsed after drag")
        return False

    def get_status(self) -> VehicleStatus:
        try:
            self.ensure_app_open()
            self._navigate_to_home()

            refresh_btn = self.driver.find_by_text("Refresh")
            if refresh_btn.exists():
                refresh_btn.click()
                time.sleep(2)

            odometer = "Unknown"
            fuel = "Unknown"
            range_val = "Unknown"
            oil = "Unknown"
            locked = False
            last_updated = "Unknown"

            odometer_elem = self.driver.find_by_resource_id(
                "com.honda.hondalink.connect:id/tv_odometer_value"
            )
            if odometer_elem.exists():
                odometer = odometer_elem.text

            fuel_elem = self.driver.find_by_resource_id(
                "com.honda.hondalink.connect:id/progressbar_fuel_level"
            )
            if fuel_elem.exists():
                fuel_text = fuel_elem.text
                if fuel_text:
                    fuel = f"{fuel_text}%"

            range_elem = self.driver.find_by_resource_id(
                "com.honda.hondalink.connect:id/tv_total_range_value"
            )
            if range_elem.exists():
                range_val = range_elem.text

            oil_elem = self.driver.find_by_resource_id(
                "com.honda.hondalink.connect:id/tv_oil_value"
            )
            if oil_elem.exists():
                oil = oil_elem.text

            lock_status_elem = self.driver.find_by_resource_id(
                "com.honda.hondalink.connect:id/textView_lockStatus"
            )
            if lock_status_elem.exists():
                lock_text = lock_status_elem.text
                locked = lock_text == "Locked"

            last_updated_elem = self.driver.find_by_resource_id(
                "com.honda.hondalink.connect:id/txt_last_updated_time"
            )
            if last_updated_elem.exists():
                last_updated = last_updated_elem.text

            current_status = VehicleStatus(
                odometer=odometer,
                fuel_level=fuel,
                range_remaining=range_val,
                oil_life=oil,
                is_locked=locked,
                last_updated=last_updated,
            )

            # Check if status is valid (not all unknown)
            if self._is_valid_status(current_status):
                logger.info("Successfully retrieved live status, caching it")
                self.last_known_status = current_status
                return current_status
            else:
                logger.warning(
                    "Live status returned all unknown values, using cached status"
                )
                if self.last_known_status:
                    return self.last_known_status
                else:
                    logger.warning(
                        "No cached status available, returning unknown status"
                    )
                    return current_status

        except Exception as e:
            logger.error(f"Failed to get live status: {e}")
            if self.last_known_status:
                logger.info("Returning last known cached status due to error")
                return self.last_known_status
            else:
                logger.error("No cached status available, re-raising exception")
                raise

    def _is_valid_status(self, status: VehicleStatus) -> bool:
        """
        Check if the status contains meaningful data (not all unknown).
        Returns True if at least one field has a non-unknown value.
        """
        return (
            status.odometer != "Unknown"
            or status.fuel_level != "Unknown"
            or status.range_remaining != "Unknown"
            or status.oil_life != "Unknown"
            or status.last_updated != "Unknown"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(CommandFailedException),
    )
    def execute_remote_command(self, command: CommandType):
        self.ensure_app_open()
        self._handle_popups()

        if not self.driver.find_by_text("Start").exists():
            if not self._expand_remote_commands_panel():
                raise CommandFailedException("Could not expand Remote Commands panel")

        btn_text = {
            CommandType.START: "Start",
            CommandType.STOP: "Stop",
            CommandType.LOCK: "Lock",
            CommandType.UNLOCK: "Unlock",
        }.get(command)

        if not btn_text:
            raise CommandFailedException(f"Unknown command {command}")

        btn = self.driver.find_by_text(btn_text)
        if not btn.exists():
            raise CommandFailedException(f"Button {btn_text} not found")

        logger.info(f"Clicking command button: {btn_text}")
        btn.click()

        logger.info("Waiting for PIN screen or result...")
        start_time = time.time()
        pin_entered = False

        while time.time() - start_time < 8:
            if self._handle_pin_entry():
                pin_entered = True
                logger.info("PIN entry flow completed")
                break

            self._handle_popups()
            time.sleep(0.2)

        if pin_entered:
            time.sleep(2)

        logger.info(f"Command {command} executed")
        return True
