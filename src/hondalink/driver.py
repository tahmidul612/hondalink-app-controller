from abc import ABC, abstractmethod
from typing import Protocol


class UIElement(Protocol):
    @property
    def text(self) -> str: ...

    def click(self) -> None: ...
    def exists(self) -> bool: ...
    def wait(self, timeout: float = 10.0) -> bool: ...
    def set_text(self, text: str) -> None: ...
    def bounds(self) -> tuple[int, int, int, int]: ...


class AndroidDriver(ABC):
    @abstractmethod
    def connect(self, address: str | None = None) -> None:
        """Connect to the device."""
        pass

    @abstractmethod
    def app_start(self, package_name: str, stop: bool = False) -> None:
        """Start an application."""
        pass

    @abstractmethod
    def app_stop(self, package_name: str) -> None:
        """Stop an application."""
        pass

    @abstractmethod
    def app_current(self) -> dict:
        """Get current app info (package, activity)."""
        pass

    @abstractmethod
    def find_by_text(self, text: str) -> UIElement:
        """Find element by exact text."""
        pass

    @abstractmethod
    def find_by_xpath(self, xpath: str) -> UIElement:
        """Find element by xpath."""
        pass

    @abstractmethod
    def find_by_resource_id(self, resource_id: str) -> UIElement:
        """Find element by resource ID."""
        pass

    @abstractmethod
    def press(self, key: str) -> None:
        """Press a hardware key (home, back, etc)."""
        pass

    @abstractmethod
    def swipe(
        self, fx: float, fy: float, tx: float, ty: float, duration: float = 0.5
    ) -> None:
        """
        Swipe from (fx, fy) to (tx, ty).

        Args:
            fx: Starting x coordinate (0.0-1.0 for normalized, or pixel value)
            fy: Starting y coordinate (0.0-1.0 for normalized, or pixel value)
            tx: Ending x coordinate (0.0-1.0 for normalized, or pixel value)
            ty: Ending y coordinate (0.0-1.0 for normalized, or pixel value)
            duration: Duration of swipe in seconds
        """
        pass

    @abstractmethod
    def dump_hierarchy(self) -> str:
        """Return the XML hierarchy."""
        pass
