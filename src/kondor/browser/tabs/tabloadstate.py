from PySide6.QtCore import Property, QUrl, Signal, Slot

from kondor.browser.tabs.assignandnotify import assign_and_notify
from kondor.browser.tabs.tabcommands import TabCommands


class TabLoadState(TabCommands):
    titleChanged = Signal()
    iconUrlChanged = Signal()
    progressChanged = Signal()
    loadingChanged = Signal()
    canGoBackChanged = Signal()
    canGoForwardChanged = Signal()
    zoomFactorChanged = Signal()

    def _init_load_state(self) -> None:
        self._title = ""
        self._icon_url = QUrl()
        self._progress = 0.0
        self._loading = False
        self._can_go_back = False
        self._can_go_forward = False
        self._zoom_factor = 1.0

    title = Property(str, lambda self: self._title, notify=titleChanged)
    iconUrl = Property(QUrl, lambda self: self._icon_url, notify=iconUrlChanged)
    progress = Property(float, lambda self: self._progress, notify=progressChanged)
    loading = Property(bool, lambda self: self._loading, notify=loadingChanged)
    canGoBack = Property(bool, lambda self: self._can_go_back, notify=canGoBackChanged)
    canGoForward = Property(bool, lambda self: self._can_go_forward, notify=canGoForwardChanged)
    zoomFactor = Property(float, lambda self: self._zoom_factor, notify=zoomFactorChanged)

    @Slot(str)
    def setTitle(self, title: str) -> None:
        assign_and_notify((self, "_title"), title, self.titleChanged)

    @Slot(QUrl)
    def setIconUrl(self, icon_url: QUrl) -> None:
        if icon_url.isEmpty():
            return
        assign_and_notify((self, "_icon_url"), icon_url, self.iconUrlChanged)

    def _clear_icon_url(self) -> None:
        assign_and_notify((self, "_icon_url"), QUrl(), self.iconUrlChanged)

    @Slot(float)
    def setProgress(self, progress: float) -> None:
        assign_and_notify((self, "_progress"), progress, self.progressChanged)

    @Slot(bool)
    def setLoading(self, loading: bool) -> None:
        assign_and_notify((self, "_loading"), loading, self.loadingChanged)

    @Slot(bool)
    def setCanGoBack(self, can_go_back: bool) -> None:
        assign_and_notify((self, "_can_go_back"), can_go_back, self.canGoBackChanged)

    @Slot(bool)
    def setCanGoForward(self, can_go_forward: bool) -> None:
        assign_and_notify((self, "_can_go_forward"), can_go_forward, self.canGoForwardChanged)

    @Slot(float)
    def setZoomFactor(self, factor: float) -> None:
        assign_and_notify((self, "_zoom_factor"), factor, self.zoomFactorChanged)
