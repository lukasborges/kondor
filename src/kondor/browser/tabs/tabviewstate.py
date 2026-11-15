from PySide6.QtCore import Property, Signal, Slot

from kondor.browser.tabs.assignandnotify import assign_and_notify
from kondor.browser.tabs.tabloadstate import TabLoadState


class TabViewState(TabLoadState):
    pinnedChanged = Signal()
    findResultChanged = Signal()
    fullScreenChanged = Signal()
    devToolsOpenChanged = Signal()
    readerAvailableChanged = Signal()
    readerActiveChanged = Signal()
    crashChanged = Signal()

    def _init_view_state(self) -> None:
        self._pinned = False
        self._find_matches = 0
        self._find_active_match = 0
        self._is_full_screen = False
        self._dev_tools_open = False
        self._reader_available = False
        self._reader_active = False
        self._crashed = False
        self._crash_reason = ""
        self._crash_exit_code = 0

    pinned = Property(bool, lambda self: self._pinned, notify=pinnedChanged)
    findMatches = Property(int, lambda self: self._find_matches, notify=findResultChanged)
    findActiveMatch = Property(int, lambda self: self._find_active_match, notify=findResultChanged)
    isFullScreen = Property(bool, lambda self: self._is_full_screen, notify=fullScreenChanged)
    devToolsOpen = Property(bool, lambda self: self._dev_tools_open, notify=devToolsOpenChanged)
    readerAvailable = Property(
        bool, lambda self: self._reader_available, notify=readerAvailableChanged
    )
    readerActive = Property(bool, lambda self: self._reader_active, notify=readerActiveChanged)
    crashed = Property(bool, lambda self: self._crashed, notify=crashChanged)
    crashReason = Property(str, lambda self: self._crash_reason, notify=crashChanged)
    crashExitCode = Property(int, lambda self: self._crash_exit_code, notify=crashChanged)

    def set_pinned(self, pinned: bool) -> None:
        assign_and_notify((self, "_pinned"), pinned, self.pinnedChanged)

    @Slot(bool)
    def setFullScreen(self, full_screen: bool) -> None:
        assign_and_notify((self, "_is_full_screen"), full_screen, self.fullScreenChanged)

    @Slot(bool)
    def setDevToolsOpen(self, is_open: bool) -> None:
        assign_and_notify((self, "_dev_tools_open"), is_open, self.devToolsOpenChanged)

    @Slot(bool)
    def setReaderAvailable(self, available: bool) -> None:
        assign_and_notify((self, "_reader_available"), available, self.readerAvailableChanged)

    @Slot(bool)
    def setReaderActive(self, active: bool) -> None:
        assign_and_notify((self, "_reader_active"), active, self.readerActiveChanged)

    @Slot(int, int)
    def setFindResult(self, matches: int, active_match: int) -> None:
        if (self._find_matches, self._find_active_match) == (matches, active_match):
            return
        self._find_matches, self._find_active_match = matches, active_match
        self.findResultChanged.emit()

    @Slot(bool)
    @Slot(bool, str)
    @Slot(bool, str, int)
    def setCrashed(self, crashed: bool, reason: str = "", exit_code: int = 0) -> None:
        current = (self._crashed, self._crash_reason, self._crash_exit_code)
        if current == (crashed, reason, exit_code):
            return
        self._crashed = crashed
        self._crash_reason = reason if crashed else ""
        self._crash_exit_code = exit_code if crashed else 0
        self.crashChanged.emit()
