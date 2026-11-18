from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from kondor.browser.agent import agentinheritance
from kondor.browser.tabs.assignandnotify import assign_and_notify

WORKING_MILLISECONDS = 10000


class TabAgent(QObject):
    accessChanged = Signal()
    targetIdChanged = Signal()
    workingNameChanged = Signal()

    def __init__(self, is_private: bool, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._is_private = is_private
        self._has_access = False
        self._name = ""
        self._target_id = ""
        self._working_name = ""
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.setInterval(WORKING_MILLISECONDS)
        self._idle_timer.timeout.connect(lambda: self._set_working_name(""))

    hasAccess = Property(bool, lambda self: self._has_access, notify=accessChanged)
    name = Property(str, lambda self: self._name, notify=accessChanged)
    targetId = Property(str, lambda self: self._target_id, notify=targetIdChanged)
    workingName = Property(str, lambda self: self._working_name, notify=workingNameChanged)

    @Slot(str)
    def grant(self, name: str) -> None:
        if self._is_private or (self._has_access and self._name == name):
            return
        self._has_access, self._name = True, name
        self.accessChanged.emit()

    @Slot()
    def allow(self) -> None:
        self.grant("")

    @Slot()
    def remove(self) -> None:
        if not self._has_access:
            return
        self._has_access, self._name = False, ""
        self.accessChanged.emit()

    @Slot(QObject)
    def passOnTo(self, request: QObject) -> None:
        if self._has_access:
            agentinheritance.remember(request, self._name)

    def inherit_for(self, request: QObject) -> None:
        name = agentinheritance.take(request)
        if name is not None:
            self.grant(name)

    @Slot(str)
    def setTargetId(self, target_id: str) -> None:
        assign_and_notify((self, "_target_id"), target_id, self.targetIdChanged)

    def note_activity(self, name: str) -> None:
        self._set_working_name(name or self._name or "An agent")
        self._idle_timer.start()

    def _set_working_name(self, name: str) -> None:
        assign_and_notify((self, "_working_name"), name, self.workingNameChanged)
