from dataclasses import dataclass

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from pytests.settings.settingswindowharness import SettingsWindowHarness

PAGE_TITLES = ["General", "Search", "Downloads", "Privacy"]
ALL_PAGES = 7
LISTED_ENTRIES = 4


@dataclass(frozen=True)
class Page:
    index: int
    title: str


def visible_page_count(harness: SettingsWindowHarness) -> int:
    return int(harness.child("pageList").property("count"))


def entry_center(entry: QQuickItem) -> QPoint:
    center = entry.mapToScene(QPointF(entry.width() / 2, entry.height() / 2))
    return QPoint(round(center.x()), round(center.y()))


def type_text(harness: SettingsWindowHarness, text: str) -> None:
    for character in text:
        QTest.keyClick(harness.window, character)


def search_for(harness: SettingsWindowHarness, text: str) -> None:
    QTest.keyClick(harness.window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(harness.window, Qt.Key.Key_Delete)
    type_text(harness, text)


def verify_sidebar_highlights(harness: SettingsWindowHarness, page: int) -> None:
    for index in range(LISTED_ENTRIES):
        entry = harness.sidebar_entry(index)
        assert entry is not None
        assert entry.property("highlighted") is (index == page)


def verify_shown_page(harness: SettingsWindowHarness, page: int, title: str) -> None:
    assert harness.window.property("currentPage") == page
    assert harness.child("pageHeading").property("text") == title
    assert harness.child("pageStack").property("currentIndex") == page
    assert harness.child("pageList").property("currentIndex") == page
    verify_sidebar_highlights(harness, page)


def verify_only_page_is_listed(harness: SettingsWindowHarness, qtbot: QtBot, page: Page) -> None:
    qtbot.waitUntil(lambda: visible_page_count(harness) == 1)
    assert harness.window.property("currentPage") == page.index
    assert harness.child("pageHeading").property("text") == page.title


def click_sidebar_entry_and_verify(
    harness: SettingsWindowHarness, qtbot: QtBot, page: Page
) -> None:
    qtbot.waitUntil(lambda: harness.sidebar_entry(page.index) is not None)
    entry = harness.sidebar_entry(page.index)
    assert isinstance(entry, QQuickItem)
    QTest.mouseClick(
        harness.window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        entry_center(entry),
    )
    qtbot.waitUntil(lambda: harness.window.property("currentPage") == page.index)
    verify_shown_page(harness, page.index, page.title)


def verify_privacy_is_the_only_entry(harness: SettingsWindowHarness, qtbot: QtBot) -> None:
    verify_only_page_is_listed(harness, qtbot, Page(3, "Privacy"))
    assert harness.child("pageStack").property("currentIndex") == 3  # noqa: PLR2004
    qtbot.waitUntil(lambda: harness.sidebar_entry(0) is not None)
    privacy = harness.sidebar_entry(0)
    assert privacy is not None
    assert privacy.property("text") == "Privacy"
    assert privacy.property("highlighted") is True
    assert harness.sidebar_entry(1) is None


def focus_search_field(harness: SettingsWindowHarness) -> bool:
    field = find_by_class_name(harness.window, "SearchField")
    if not isinstance(field, QQuickItem):
        return False
    field.forceActiveFocus()
    return True


def find_by_class_name(parent: QObject, class_name: str) -> QObject | None:
    for child in parent.children():
        if class_name in child.metaObject().className():
            return child
        found = find_by_class_name(child, class_name)
        if found is not None:
            return found
    return None
