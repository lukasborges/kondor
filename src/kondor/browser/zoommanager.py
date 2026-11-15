from PySide6.QtCore import QObject, QSettings, QUrl, Signal, Slot

ORGANIZATION = "KDE"
APPLICATION = "Kondor"
GROUP = "SiteZoom"
EPSILON = 0.001
DEFAULT_ZOOM = 1.0
WEB_SCHEMES = ("http", "https")
LEVELS = (0.3, 0.5, 0.67, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0)


def settings_path(host: str) -> str:
    return f"{GROUP}/{host.replace('/', '_')}"


def is_default_zoom(factor: float) -> bool:
    return abs(factor - DEFAULT_ZOOM) < EPSILON


def as_real(value: object) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def next_level_above(current: float) -> float:
    return next((level for level in LEVELS if level > current + EPSILON), LEVELS[-1])


def next_level_below(current: float) -> float:
    below = (level for level in reversed(LEVELS) if level < current - EPSILON)
    return next(below, LEVELS[0])


class ZoomManager(QObject):
    zoomChanged = Signal(str, float)
    _instance: "ZoomManager | None" = None

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings(ORGANIZATION, APPLICATION)

    @classmethod
    def instance(cls) -> "ZoomManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @Slot(QUrl, result=str)
    def hostOf(self, url: QUrl) -> str:
        if url.scheme() not in WEB_SCHEMES:
            return ""
        return str(url.host()).lower()

    @Slot(str, result=float)
    def zoomFor(self, host: str) -> float:
        if not host:
            return DEFAULT_ZOOM
        factor = as_real(self._settings.value(settings_path(host), DEFAULT_ZOOM))
        return factor if factor > 0 else DEFAULT_ZOOM

    @Slot(str, float)
    def setZoomFor(self, host: str, factor: float) -> None:
        if not host or abs(self.zoomFor(host) - factor) < EPSILON / 10:
            return
        self.store_zoom(host, factor)
        self.zoomChanged.emit(host, DEFAULT_ZOOM if is_default_zoom(factor) else factor)

    @Slot(float, int, result=float)
    def step(self, current: float, direction: int) -> float:
        return next_level_above(current) if direction > 0 else next_level_below(current)

    def store_zoom(self, host: str, factor: float) -> None:
        if is_default_zoom(factor):
            self._settings.remove(settings_path(host))
        else:
            self._settings.setValue(settings_path(host), factor)
        self._settings.sync()
