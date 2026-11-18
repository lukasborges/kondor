from PySide6.QtCore import Property, QObject, Signal, Slot

from kondor.browser.tabs.assignandnotify import assign_and_notify

GROUP_COLORS = ("blue", "green", "orange", "red", "purple", "gray")


class TabGroup(QObject):
    nameChanged = Signal()
    colorChanged = Signal()
    collapsedChanged = Signal()

    def __init__(self, name: str = "", color: str = GROUP_COLORS[0], parent: QObject | None = None):
        super().__init__(parent)
        self._name = name
        self._color = color if color in GROUP_COLORS else GROUP_COLORS[0]
        self._collapsed = False

    @Slot(str)
    def setName(self, name: str) -> None:
        assign_and_notify((self, "_name"), name, self.nameChanged)

    @Slot(str)
    def setColor(self, color: str) -> None:
        if color in GROUP_COLORS:
            assign_and_notify((self, "_color"), color, self.colorChanged)

    def set_collapsed(self, collapsed: bool) -> None:
        assign_and_notify((self, "_collapsed"), collapsed, self.collapsedChanged)

    name = Property(str, lambda self: self._name, setName, notify=nameChanged)
    color = Property(str, lambda self: self._color, setColor, notify=colorChanged)
    collapsed = Property(bool, lambda self: self._collapsed, notify=collapsedChanged)
