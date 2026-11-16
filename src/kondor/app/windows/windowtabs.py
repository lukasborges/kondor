from collections.abc import Iterable

from PySide6.QtCore import QObject

from kondor.app.instance.windowactivation import raise_window
from kondor.browser.tabs.tabmodel import TabModel


def index_in_window(window: QObject, tab: QObject) -> tuple[TabModel | None, int]:
    model = window.findChild(TabModel)
    return (model, int(model.indexOfTab(tab))) if model is not None else (None, -1)


def show_tab_in(windows: Iterable[QObject], tab: QObject, token: bytes) -> bool:
    for window in windows:
        model, index = index_in_window(window, tab)
        if model is not None and index >= 0:
            model.setCurrentIndex(index)
            raise_window(window, token)
            return True
    return False
