from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QIODevice,
    QObject,
    QSaveFile,
    QStandardPaths,
    QTimer,
    QUrl,
    Slot,
    qWarning,
)
from shiboken6 import isValid

from kondor.browser.session import sessionformat
from kondor.browser.session.sessionwindow import SessionTab, SessionWindow
from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from kondor.browser.tabs.tabmodelrows import TAB_ROLE

AUTOSAVE_DELAY_MS = 2000


def tab_at(model: TabModel, row: int) -> Tab | None:
    tab = model.data(model.index(row, 0), TAB_ROLE)
    return tab if isinstance(tab, Tab) else None


def session_tab_of(tab: Tab) -> SessionTab:
    return SessionTab(QUrl() if tab.newTabPage else tab.url, tab.title)


def session_window_of(model: TabModel) -> SessionWindow:
    window = SessionWindow()
    for row in range(model.count):
        tab = tab_at(model, row)
        if tab is None or tab.isPrivate:
            continue
        if row == model.currentIndex:
            window.current_index = len(window.tabs)
        window.tabs.append(session_tab_of(tab))
    return window


def session_file_path() -> Path:
    folder = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "session.json"


def write_session_file(content: bytes) -> None:
    file = QSaveFile(str(session_file_path()))
    if not file.open(QIODevice.OpenModeFlag.WriteOnly):
        qWarning(f"Kondor: cannot write the session file {file.fileName()}")
        return
    file.write(content)
    if not file.commit():
        qWarning(f"Kondor: cannot commit the session file {file.fileName()}")


class SessionManager(QObject):
    _instance: "SessionManager | None" = None

    def __init__(self) -> None:
        super().__init__()
        self._models: list[TabModel] = []
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(AUTOSAVE_DELAY_MS)
        self._save_timer.timeout.connect(self.save_now)
        app = QCoreApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.save_now)

    @classmethod
    def instance(cls) -> "SessionManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @Slot(TabModel)
    def watch(self, model: TabModel | None) -> None:
        if model is None or model in self._models:
            return
        self._prune_models()
        self._models.append(model)
        self._connect_model(model)
        self._track_rows(model, 0, model.count - 1)

    def _connect_model(self, model: TabModel) -> None:
        model.countChanged.connect(self._schedule_save)
        model.currentIndexChanged.connect(self._schedule_save)
        model.rowsRemoved.connect(self._schedule_save)
        model.destroyed.connect(self._forget_destroyed_model)
        model.rowsInserted.connect(
            lambda _parent, first, last: self._rows_inserted(model, first, last)
        )

    def _rows_inserted(self, model: TabModel, first: int, last: int) -> None:
        self._track_rows(model, first, last)
        self._schedule_save()

    def _forget_destroyed_model(self) -> None:
        self._prune_models()
        self._schedule_save()

    def _track_rows(self, model: TabModel, first: int, last: int) -> None:
        for row in range(first, min(last, model.count - 1) + 1):
            tab = tab_at(model, row)
            if tab is not None:
                tab.urlChanged.connect(self._schedule_save)

    def _prune_models(self) -> None:
        self._models = [model for model in self._models if isValid(model)]

    def _schedule_save(self) -> None:
        self._save_timer.start()

    @Slot(TabModel)
    def save(self, model: TabModel | None) -> None:
        if model is not None:
            self.watch(model)
        self.save_now()

    def _has_normal_window(self) -> bool:
        return any(not model.privateTabs for model in self._models)

    def _collect_windows(self) -> list[SessionWindow]:
        windows = [session_window_of(model) for model in self._models]
        return [window for window in windows if window.tabs]

    def save_now(self) -> None:
        self._save_timer.stop()
        self._prune_models()
        if self._has_normal_window():
            write_session_file(sessionformat.to_json(self._collect_windows()))

    def saved_windows(self) -> list[SessionWindow]:
        try:
            return sessionformat.from_json(session_file_path().read_bytes())
        except OSError:
            return []
