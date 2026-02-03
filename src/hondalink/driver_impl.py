
import uiautomator2 as u2

from .driver import AndroidDriver, UIElement


class U2ElementWrapper:
    def __init__(self, element):
        self._element = element

    @property
    def text(self) -> str:
        return self._element.get_text()

    def click(self) -> None:
        self._element.click()

    def exists(self) -> bool:
        return self._element.exists

    def wait(self, timeout: float = 10.0) -> bool:
        return self._element.wait(timeout=timeout)

    def set_text(self, text: str) -> None:
        self._element.set_text(text)


class UiautomatorDriver(AndroidDriver):
    def __init__(self):
        self.d = None

    def connect(self, address: str | None = None) -> None:
        if address:
            self.d = u2.connect(address)
        else:
            self.d = u2.connect()

    def app_start(self, package_name: str, stop: bool = False) -> None:
        if self.d:
            self.d.app_start(package_name, stop=stop)

    def app_stop(self, package_name: str) -> None:
        if self.d:
            self.d.app_stop(package_name)

    def app_current(self) -> dict:
        if self.d:
            return self.d.app_current()
        return {}

    def find_by_text(self, text: str) -> UIElement:
        return U2ElementWrapper(self.d(text=text))

    def find_by_xpath(self, xpath: str) -> UIElement:
        return U2ElementWrapper(self.d.xpath(xpath))

    def find_by_resource_id(self, resource_id: str) -> UIElement:
        return U2ElementWrapper(self.d(resourceId=resource_id))

    def press(self, key: str) -> None:
        if self.d:
            self.d.press(key)

    def dump_hierarchy(self) -> str:
        if self.d:
            return self.d.dump_hierarchy()
        return ""
