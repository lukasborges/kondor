from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.popups.popupurl import is_web_address
from kondor.browser.responsive import devices, ratios
from kondor.browser.responsive.responsiveagent import ResponsiveAgent
from kondor.browser.responsive.responsivememory import ResponsiveMemory
from kondor.browser.tabs.assignandnotify import assign_and_notify


class TabResponsive(QObject):
    activeChanged = Signal()
    deviceChanged = Signal()
    sizeChanged = Signal()
    ratioChanged = Signal()
    zoomToFitChanged = Signal()
    reloadRequested = Signal()

    def __init__(
        self, profile: QQuickWebEngineProfile | None, is_private: bool, parent: QObject
    ) -> None:
        super().__init__(parent)
        self._agent = ResponsiveAgent(profile)
        self.destroyed.connect(self._agent.release)
        self._profile = profile
        self._memory = ResponsiveMemory(is_private)
        self._host = ""
        self._is_active = False
        self._zoom_to_fit = True
        self._device, (self._width, self._height) = self._memory.recall()
        self._ratio = self._initial_ratio()

    isActive = Property(bool, lambda self: self._is_active, notify=activeChanged)
    device = Property(str, lambda self: self._device, notify=deviceChanged)
    width = Property(int, lambda self: self._width, notify=sizeChanged)
    height = Property(int, lambda self: self._height, notify=sizeChanged)
    ratio = Property(float, lambda self: self._ratio, notify=ratioChanged)
    maxRatio = Property(
        float, lambda self: ratios.max_ratio(self._width, self._height), notify=sizeChanged
    )
    ratioList = Property("QVariantList", lambda self: list(ratios.RATIOS), constant=True)
    zoomToFit = Property(bool, lambda self: self._zoom_to_fit, notify=zoomToFitChanged)
    deviceList = Property("QVariantList", lambda self: devices.device_list(), constant=True)

    @Slot(bool)
    def setActive(self, active: bool) -> None:
        assign_and_notify((self, "_is_active"), active, self.activeChanged)
        self._sync_agent()
        if not active:
            self.rememberSize()

    @Slot()
    def toggle(self) -> None:
        self.setActive(not self._is_active)

    @Slot(str)
    def selectDevice(self, key: str) -> None:
        device = devices.device_for(key)
        if device is None:
            self._select_responsive()
            return
        self._set_size(device.width, device.height)
        self._set_ratio(device.ratio)
        self._set_device(key)
        self.rememberSize()

    @Slot(float)
    def setRatio(self, ratio: float) -> None:
        self._set_ratio(ratios.fitted(ratio, self._width, self._height))
        if self._device == devices.RESPONSIVE:
            self._memory.remember_ratio(self._ratio)

    @Slot(int, int)
    def setSize(self, width: int, height: int) -> None:
        self._set_size(devices.clamped(width), devices.clamped(height))
        self._set_device(devices.RESPONSIVE)

    @Slot(int, int)
    def commitSize(self, width: int, height: int) -> None:
        self.setSize(width, height)
        self.rememberSize()

    @Slot()
    def rememberSize(self) -> None:
        self._memory.remember_size(self._width, self._height)
        if self._device == devices.RESPONSIVE:
            self._memory.remember_ratio(self._ratio)

    @Slot()
    def rotate(self) -> None:
        self._set_size(self._height, self._width)
        self.rememberSize()

    @Slot(bool)
    def setZoomToFit(self, zoom_to_fit: bool) -> None:
        assign_and_notify((self, "_zoom_to_fit"), zoom_to_fit, self.zoomToFitChanged)

    def update_for(self, url: QUrl) -> None:
        host = url.host().lower() if is_web_address(url) else ""
        if host == self._host:
            return
        self._host = host
        self._sync_agent()

    def _set_device(self, key: str) -> None:
        assign_and_notify((self, "_device"), key, self.deviceChanged)
        self._memory.remember_device(self._device)
        self._sync_agent()

    def _set_size(self, width: int, height: int) -> None:
        if (width, height) == (self._width, self._height):
            return
        self._width, self._height = width, height
        self.sizeChanged.emit()
        self._set_ratio(ratios.fitted(self._ratio, width, height))

    def _set_ratio(self, ratio: float) -> None:
        assign_and_notify((self, "_ratio"), ratio, self.ratioChanged)

    def _select_responsive(self) -> None:
        self._set_device(devices.RESPONSIVE)
        self.setRatio(self._memory.recall_ratio())

    def _initial_ratio(self) -> float:
        device = devices.device_for(self._device)
        wanted = device.ratio if device else self._memory.recall_ratio()
        return ratios.fitted(wanted, self._width, self._height)

    def _wanted_agent(self) -> str:
        if not self._is_active or self._profile is None:
            return ""
        return devices.mobile_agent(self._device, self._profile.httpUserAgent())

    def _sync_agent(self) -> None:
        if self._agent.sync(self._host, self._wanted_agent()) and self._host:
            self.reloadRequested.emit()
