from PySide6.QtCore import Property, QAbstractItemModel, QDateTime, QObject, QUrl, Slot

from kondor.browser.favicons.faviconstore import FaviconStore
from kondor.core.database import sql
from kondor.history import historysearch, topsitesranking
from kondor.history.historymodel import HistoryModel

RECENT_VISIT_WINDOW_MS = 30000
TRACKED_SCHEMES = ("http", "https", "file")
DEFAULT_SUGGESTION_LIMIT = 6
LATEST_VISIT = "SELECT id, url, visited_at FROM history ORDER BY visited_at DESC, id DESC LIMIT 1"
RECENT_VISIT_OF_URL = (
    "SELECT id FROM history WHERE url = ? AND visited_at >= ?"
    " ORDER BY visited_at DESC, id DESC LIMIT 1"
)
UPDATE_TITLE = "UPDATE history SET title = ? WHERE id = ?"
INSERT_VISIT = "INSERT INTO history (url, title, visited_at) VALUES (?, ?, ?)"
DELETE_ENTRY = "DELETE FROM history WHERE id = ?"
DELETE_ALL = "DELETE FROM history"
DELETE_SINCE = "DELETE FROM history WHERE visited_at >= ?"


def is_tracked(url: QUrl) -> bool:
    return not url.isEmpty() and url.scheme() in TRACKED_SCHEMES


def recent_visit_id_of(url: str, now: int) -> int | None:
    last = sql.run(LATEST_VISIT)
    if last is None or not last.next():
        return None
    is_same_url = str(last.value(1)) == url
    is_recent = now - int(last.value(2)) < RECENT_VISIT_WINDOW_MS
    return int(last.value(0)) if is_same_url and is_recent else None


def update_title_of(entry_id: int, title: str) -> None:
    sql.run(UPDATE_TITLE, (title, entry_id))


def merge_into_recent_visit(url: str, title: str, now: int) -> bool:
    recent_id = recent_visit_id_of(url, now)
    if recent_id is not None:
        update_title_of(recent_id, title)
    return recent_id is not None


def insert_visit(url: str, title: str, now: int) -> bool:
    return sql.run(INSERT_VISIT, (url, title, now)) is not None


class HistoryManager(QObject):
    _instance: "HistoryManager | None" = None

    def __init__(self) -> None:
        super().__init__()
        self._model = HistoryModel(self)

    @classmethod
    def instance(cls) -> "HistoryManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def history_model(self) -> HistoryModel:
        return self._model

    model = Property(QAbstractItemModel, history_model, constant=True)

    @Slot(QUrl, str)
    def addVisit(self, url: QUrl, title: str) -> None:
        if not is_tracked(url):
            return
        address, now = url.toString(), QDateTime.currentMSecsSinceEpoch()
        if merge_into_recent_visit(address, title, now) or insert_visit(address, title, now):
            self._model.schedule_refresh()

    @Slot(QUrl, str)
    def updateTitle(self, url: QUrl, title: str) -> None:
        if not is_tracked(url):
            return
        since = QDateTime.currentMSecsSinceEpoch() - RECENT_VISIT_WINDOW_MS
        ids = sql.ids(RECENT_VISIT_OF_URL, (url.toString(), since))
        if not ids:
            return
        update_title_of(ids[0], title)
        self._model.schedule_refresh()

    @Slot("qint64")
    def removeEntry(self, entry_id: int) -> None:
        if sql.run(DELETE_ENTRY, (entry_id,)) is not None:
            self._model.refresh()

    @Slot()
    def clearAll(self) -> None:
        if sql.run(DELETE_ALL) is None:
            return
        self._model.refresh()
        FaviconStore.instance().clear_all()

    @Slot("qint64")
    def clearSince(self, msecs_since_epoch: int) -> None:
        if sql.run(DELETE_SINCE, (msecs_since_epoch,)) is None:
            return
        self._model.refresh()
        FaviconStore.instance().clear_since(msecs_since_epoch)

    @Slot(int, result="QVariantList")
    def topSites(self, limit: int) -> list[dict[str, str]]:
        return topsitesranking.top_sites(limit)

    @Slot(str, result="QVariantList")
    @Slot(str, int, result="QVariantList")
    def suggest(self, text: str, limit: int = DEFAULT_SUGGESTION_LIMIT) -> list[dict[str, str]]:
        return historysearch.suggest(text, limit)

    @Slot(int, result="QVariantList")
    def recentToday(self, limit: int) -> list[dict[str, str]]:
        return historysearch.recent_today(limit)

    @Slot(str, result=str)
    def hostCompletion(self, text: str) -> str:
        return historysearch.host_completion(text)
