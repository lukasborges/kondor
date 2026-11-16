from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from kondor.bookmarks.bookmarkmanager import BookmarkManager
from kondor.core.database import sql

INSERT_VISIT = "INSERT INTO history (url, title, visited_at) VALUES (?, ?, ?)"
PLASMA_VISITED_AT = 1000000
Row = dict[str, Any]


def popup_path(staged_build: Path) -> Path:
    return staged_build / "qml" / "Kondor" / "browser" / "address" / "AddressSuggestions.qml"


def popup_component(engine: QQmlEngine, staged_build: Path) -> QQmlComponent:
    return QQmlComponent(engine, QUrl.fromLocalFile(str(popup_path(staged_build))))


def popup_typing(component: QQmlComponent, text: str) -> QObject:
    popup = component.create()
    assert popup is not None, component.errors()
    popup.setProperty("text", text)
    return popup


def rows_of(popup: QObject) -> list[Row]:
    return list(popup.property("rows").toVariant())


def field_of(rows: list[Row], row: int, key: str) -> str:
    value = rows[row].get(key, "")
    return str(value.toString() if isinstance(value, QUrl) else value)


def has_row_with_icon(rows: list[Row], icon_name: str) -> bool:
    return any(row.get("iconName") == icon_name for row in rows)


def has_row_labeled(rows: list[Row], label: str, icon_name: str | None = None) -> bool:
    matches = [row for row in rows if row.get("label") == label]
    return any(icon_name in (None, row.get("iconName")) for row in matches)


def clear_history() -> None:
    assert sql.run("DELETE FROM history") is not None


def add_history(url: str, title: str, visited_at: int) -> None:
    assert sql.run(INSERT_VISIT, (url, title, visited_at)) is not None


def add_plasma_history() -> None:
    add_history("https://kde.org/", "KDE Community", PLASMA_VISITED_AT - 3000)
    add_history("https://kde.org/", "KDE Community", PLASMA_VISITED_AT - 2000)
    add_history("https://plasma.kde.org/", "KDE Plasma", PLASMA_VISITED_AT - 1000)


def add_plasma_bookmark() -> int:
    bookmarks = BookmarkManager.instance()
    folder = bookmarks.addFolder("Address suggestions test", bookmarks.toolbarFolderId())
    bookmark = bookmarks.addBookmark(QUrl("https://kde.org/hig/"), "Plasma HIG", folder)
    assert bookmark > 0, "bookmark was not added"
    return folder
