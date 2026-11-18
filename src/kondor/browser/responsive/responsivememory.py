from kondor.browser.responsive import devices
from kondor.core.settings.settings import Settings

DEVICE_SETTING = "responsiveDevice"
SIZE_SETTING = "responsiveSize"


class ResponsiveMemory:
    def __init__(self, is_private: bool) -> None:
        self._is_private = is_private

    def recall(self) -> tuple[str, tuple[int, int]]:
        settings = Settings.instance()
        key = str(settings.property(DEVICE_SETTING))
        known = key == devices.RESPONSIVE or devices.device_for(key) is not None
        size = devices.parse_size(str(settings.property(SIZE_SETTING)))
        return (key if known else devices.RESPONSIVE), (size or devices.DEFAULT_SIZE)

    def remember_device(self, key: str) -> None:
        self._store(DEVICE_SETTING, key)

    def remember_size(self, width: int, height: int) -> None:
        self._store(SIZE_SETTING, devices.format_size(width, height))

    def _store(self, name: str, value: str) -> None:
        if not self._is_private:
            Settings.instance().setProperty(name, value)
