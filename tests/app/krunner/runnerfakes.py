from PySide6.QtCore import (
    Property,
    QModelIndex,
    QObject,
    Qt,
    QUrl,
    Slot,
)

from kondor.browser.tabs.tabmodel import TabModel
from kondor.browser.tabs.tabmodelrows import TAB_ROLE


class FakeTab(QObject):
    def __init__(self, title: str, url: str, is_private: bool = False) -> None:
        super().__init__()
        self._title = title
        self._url = QUrl(url)
        self._is_private = is_private

    title = Property(str, lambda self: self._title, constant=True)
    url = Property(QUrl, lambda self: self._url, constant=True)
    isPrivate = Property(bool, lambda self: self._is_private, constant=True)
    newTabPage = Property(bool, lambda self: not self._url.isValid(), constant=True)


class FakeTabModel(TabModel):
    def __init__(self, tabs: list[FakeTab]) -> None:
        super().__init__()
        self.fakes = tabs
        self.current_index = -1

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        return len(self.fakes)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> FakeTab | None:  # type: ignore[override]
        return self.fakes[index.row()] if role == TAB_ROLE else None

    @Slot(QObject, result=int)
    def indexOfTab(self, tab: QObject) -> int:  # type: ignore[override]  # noqa: N802
        return self.fakes.index(tab) if tab in self.fakes else -1

    @Slot(int)
    def setCurrentIndex(self, index: int) -> None:  # noqa: N802
        self.current_index = index


class FakeWindow(QObject):
    def __init__(self, tabs: list[FakeTab], is_private: bool = False) -> None:
        super().__init__()
        self.model = FakeTabModel(tabs)
        self.model.setParent(self)
        self._is_private = is_private

    privateWindow = Property(bool, lambda self: self._is_private, constant=True)
