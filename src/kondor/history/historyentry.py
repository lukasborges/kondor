from collections.abc import Callable
from enum import IntEnum
from typing import NamedTuple

from PySide6.QtCore import QByteArray, QCoreApplication, QDate, QDateTime, QLocale, Qt, QUrl
from PySide6.QtSql import QSqlQuery


class Roles(IntEnum):
    IdRole = Qt.ItemDataRole.UserRole + 1
    UrlRole = Qt.ItemDataRole.UserRole + 2
    TitleRole = Qt.ItemDataRole.UserRole + 3
    VisitedAtRole = Qt.ItemDataRole.UserRole + 4
    DayLabelRole = Qt.ItemDataRole.UserRole + 5
    TimeRole = Qt.ItemDataRole.UserRole + 6


ROLE_NAMES = {
    Roles.IdRole: b"id",
    Roles.UrlRole: b"url",
    Roles.TitleRole: b"title",
    Roles.VisitedAtRole: b"visitedAt",
    Roles.DayLabelRole: b"dayLabel",
    Roles.TimeRole: b"time",
}


class HistoryEntry(NamedTuple):
    id: int
    url: QUrl
    title: str
    visited_at: QDateTime
    day_label: str


def day_label_of(time: QDateTime) -> str:
    date = time.date()
    today = QDate.currentDate()
    if date == today:
        return str(QCoreApplication.translate("HistoryModel", "Today"))
    if date == today.addDays(-1):
        return str(QCoreApplication.translate("HistoryModel", "Yesterday"))
    return str(QLocale().toString(date, QLocale.FormatType.LongFormat))


def time_label_of(time: QDateTime) -> str:
    return str(QLocale().toString(time.time(), QLocale.FormatType.ShortFormat))


def entry_of(row: QSqlQuery) -> HistoryEntry:
    visited_at = QDateTime.fromMSecsSinceEpoch(int(row.value(3)))
    url, title = QUrl(str(row.value(1))), str(row.value(2))
    return HistoryEntry(int(row.value(0)), url, title, visited_at, day_label_of(visited_at))


ROLE_READERS: dict[int, Callable[[HistoryEntry], object]] = {
    Roles.IdRole: lambda entry: entry.id,
    Roles.UrlRole: lambda entry: entry.url.toString(),
    Roles.TitleRole: lambda entry: entry.title,
    Roles.VisitedAtRole: lambda entry: entry.visited_at,
    Roles.DayLabelRole: lambda entry: entry.day_label,
    Roles.TimeRole: lambda entry: time_label_of(entry.visited_at),
}


def role_value(entry: HistoryEntry, role: int) -> object:
    reader = ROLE_READERS.get(role)
    return None if reader is None else reader(entry)


def role_names() -> dict[int, QByteArray]:
    return {role: QByteArray(name) for role, name in ROLE_NAMES.items()}
