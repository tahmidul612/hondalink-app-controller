from .driver import AndroidDriver, UIElement


class MockElement:
    def __init__(
        self,
        text: str = "",
        exists: bool = True,
        bounds: tuple[int, int, int, int] | None = None,
    ):
        self._text = text
        self._exists = exists
        self._bounds = bounds or (0, 0, 100, 100)
        self.clicked = False
        self.input_text = None

    @property
    def text(self) -> str:
        return self._text

    def click(self) -> None:
        self.clicked = True

    def exists(self) -> bool:
        return self._exists

    def wait(self, timeout: float = 10.0) -> bool:
        return self._exists

    def set_text(self, text: str) -> None:
        self.input_text = text

    def bounds(self) -> tuple[int, int, int, int]:
        return self._bounds


class MockDriver(AndroidDriver):
    def __init__(self):
        self.connected = False
        self.current_package = None
        self.pressed_keys: list[str] = []
        # specific mocks
        self.elements: dict[str, MockElement] = {}
        self.default_element = MockElement(exists=False)

    def connect(self, address: str | None = None) -> None:
        self.connected = True

    def app_start(self, package_name: str, stop: bool = False) -> None:
        self.current_package = package_name

    def app_stop(self, package_name: str) -> None:
        if self.current_package == package_name:
            self.current_package = None

    def app_current(self) -> dict:
        return {"package": self.current_package, "activity": "MainActivity"}

    def _get_element(self, key: str) -> UIElement:
        return self.elements.get(key, MockElement(exists=False))

    def find_by_text(self, text: str) -> UIElement:
        return self._get_element(f"text={text}")

    def find_by_xpath(self, xpath: str) -> UIElement:
        return self._get_element(f"xpath={xpath}")

    def find_by_resource_id(self, resource_id: str) -> UIElement:
        return self._get_element(f"id={resource_id}")

    def press(self, key: str) -> None:
        self.pressed_keys.append(key)

    def swipe(
        self, fx: float, fy: float, tx: float, ty: float, duration: float = 0.5
    ) -> None:
        pass

    def dump_hierarchy(self) -> str:
        return "<mock>hierarchy</mock>"

    def register_element(
        self,
        selector: str,
        text: str = "",
        exists: bool = True,
        bounds: tuple[int, int, int, int] | None = None,
    ) -> MockElement:
        """
        Selector examples: 'text=Start', 'xpath=//button', 'id=com.honda:id/btn'
        """
        elem = MockElement(text=text, exists=exists, bounds=bounds)
        self.elements[selector] = elem
        return elem
