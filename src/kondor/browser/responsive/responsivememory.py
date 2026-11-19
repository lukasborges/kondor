from kondor.browser.responsive import devices, ratios
from kondor.core.settings.settings import Settings

DEVICE_SETTING = "responsiveDevice"
SIZE_SETTING = "responsiveSize"
RATIO_SETTING = "responsiveRatio"


class ResponsiveMemory:
    def __init__(self, is_private: bool) -> None:
        self._is_private = is_private

    def recall(self) -> tuple[str, tuple[int, int]]:
        settings = Settings.instance()
        key = str(settings.property(DEVICE_SETTING))
        known = self._known(key)
        if known != key:
            return known, self._fallback_size()
        size = devices.parse_size(str(settings.property(SIZE_SETTING)))
        return known, (size or devices.DEFAULT_SIZE)

    def _fallback_size(self) -> tuple[int, int]:
        fallback = devices.device_for(devices.FALLBACK_DEVICE)
        return (fallback.width, fallback.height) if fallback else devices.DEFAULT_SIZE

    def recall_ratio(self) -> float:
        value = float(Settings.instance().property(RATIO_SETTING))
        return value if value > 0 else ratios.DEFAULT_RATIO

    def remember_device(self, key: str) -> None:
        self._store(DEVICE_SETTING, key)

    def remember_size(self, width: int, height: int) -> None:
        self._store(SIZE_SETTING, devices.format_size(width, height))

    def remember_ratio(self, ratio: float) -> None:
        self._store(RATIO_SETTING, ratio)

    def _known(self, key: str) -> str:
        if key == devices.RESPONSIVE or devices.device_for(key) is not None:
            return key
        return devices.FALLBACK_DEVICE

    def _store(self, name: str, value: object) -> None:
        if not self._is_private:
            Settings.instance().setProperty(name, value)
