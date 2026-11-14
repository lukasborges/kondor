from PySide6.QtCore import QDate, QDateTime, QTime
from PySide6.QtQml import QQmlEngine

from kondor.history.historyentry import Roles
from kondor.history.historymanager import HistoryManager
from kondor.history.historymodel import HistoryModel
from pytests.history.historyrows import add_visit, now_ms, titles
from pytests.qmlsupport import create_object

CLEAR_SINCE_SOURCE = """import QtQml
import Kondor

QtObject {
    Component.onCompleted: HistoryManager.clearSince(Date.now() - 2000)
}
"""


def column_of(model: HistoryModel, role: int) -> list[object]:
    return [model.data(model.index(row), role) for row in range(model.rowCount())]


def test_filter_matches_url_or_title_and_escapes_wildcards(history: HistoryManager) -> None:
    now = now_ms()
    add_visit("https://kde.org/", "KDE", now - 3000)
    add_visit("https://example.org/", "About kde", now - 2000)
    add_visit("https://example.org/a_b", "Other", now - 1000)
    model = HistoryModel()
    model.setProperty("filter", " kde ")
    assert column_of(model, Roles.TitleRole) == ["About kde", "KDE"]
    model.setProperty("filter", "_")
    assert column_of(model, Roles.UrlRole) == ["https://example.org/a_b"]


def test_day_labels_say_today_and_yesterday(history: HistoryManager) -> None:
    midnight = int(QDateTime(QDate.currentDate(), QTime(0, 0)).toMSecsSinceEpoch())
    add_visit("https://old.example/", "Yesterday", midnight - 1000)
    add_visit("https://new.example/", "Today", now_ms())
    model = HistoryModel()
    model.refresh()
    assert column_of(model, Roles.DayLabelRole) == ["Today", "Yesterday"]


def test_url_at_is_empty_outside_the_rows(history: HistoryManager) -> None:
    add_visit("https://kde.org/", "KDE", now_ms())
    model = HistoryModel()
    model.refresh()
    assert model.urlAt(0) == "https://kde.org/"
    assert model.urlAt(1) == ""
    assert model.urlAt(-1) == ""


def test_schedule_refresh_waits_until_active(history: HistoryManager) -> None:
    add_visit("https://kde.org/", "KDE", now_ms())
    model = HistoryModel()
    model.schedule_refresh()
    assert not model.is_refresh_scheduled()
    model.setProperty("active", True)
    assert model.rowCount() == 1


def test_clear_since_accepts_milliseconds_since_epoch(
    history: HistoryManager, kondor_engine: QQmlEngine
) -> None:
    add_visit("https://a.example/", "Older", now_ms() - 5000)
    add_visit("https://b.example/", "Newer", now_ms() - 1000)
    create_object(kondor_engine, CLEAR_SINCE_SOURCE)
    assert titles() == ["Older"]
