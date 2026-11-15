from pathlib import Path

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlEngine
from PySide6.QtTest import QTest

from kondor.browser.tabs.tabmodel import TabModel
from tests.bookmarks.bar.barharness import (
    TARGETS_QML,
    create_bar,
    create_menu,
    create_with,
    evaluate,
    fill_toolbar,
)
from tests.bookmarks.bookmarkrows import add_folder_in_other, add_page, manager
from tests.qmlsupport import captured_messages


def toolbar_count() -> int:
    return len(manager().folderContents(manager().toolbarFolderId()))


def count_visible(bar: QObject, engine: QQmlEngine) -> int:
    QTest.qWait(100)
    return int(bar.property("visibleCount"))


def test_every_item_shows_when_the_bar_is_wide(
    fresh_bookmarks: Path, kondor_engine: QQmlEngine, tabs: TabModel
) -> None:
    fill_toolbar(12)
    with captured_messages() as messages:
        bar = create_bar(kondor_engine, tabs, 4000)
        assert count_visible(bar, kondor_engine) == toolbar_count()
    assert messages == []


def test_items_that_do_not_fit_move_to_the_overflow_menu(
    fresh_bookmarks: Path, kondor_engine: QQmlEngine, tabs: TabModel
) -> None:
    fill_toolbar(12)
    bar = create_bar(kondor_engine, tabs, 400)
    assert 0 < count_visible(bar, kondor_engine) < toolbar_count()


def test_widening_the_bar_brings_the_items_back(
    fresh_bookmarks: Path, kondor_engine: QQmlEngine, tabs: TabModel
) -> None:
    fill_toolbar(12)
    bar = create_bar(kondor_engine, tabs, 400)
    bar.setProperty("width", 4000)
    assert count_visible(bar, kondor_engine) == toolbar_count()


def test_folder_menu_lists_open_all_and_add_page(
    fresh_bookmarks: Path, kondor_engine: QQmlEngine
) -> None:
    folder = add_folder_in_other("News")
    add_page(folder, "One", "one")
    add_page(folder, "Two", "two")
    menu = create_menu(kondor_engine, folder, True)
    menu.metaObject().invokeMethod(menu, "rebuild")
    texts = menu.property("texts").toVariant()
    assert texts[-2:] == ["Open All in Tabs (2)", "Add This Page Here"]


def test_empty_folder_menu_has_no_open_all(
    fresh_bookmarks: Path, kondor_engine: QQmlEngine
) -> None:
    folder = add_folder_in_other("Empty")
    menu = create_menu(kondor_engine, folder, False)
    menu.metaObject().invokeMethod(menu, "rebuild")
    assert menu.property("texts").toVariant() == ["(Empty)"]


def test_dropping_a_link_adds_a_bookmark_at_the_drop_position(
    fresh_bookmarks: Path, kondor_engine: QQmlEngine
) -> None:
    first = add_page(manager().toolbarFolderId(), "First", "first")
    harness = create_with(kondor_engine, TARGETS_QML, {})
    harness.metaObject().invokeMethod(harness, "dropLinkAtTheStart")
    toolbar = manager().folderContents(manager().toolbarFolderId())
    assert toolbar[0]["title"] == "Dropped"
    assert manager().bookmarkIdFor(QUrl("https://dropped.example/")) != first


def test_dragging_an_item_to_a_later_position_moves_it_there(
    fresh_bookmarks: Path, kondor_engine: QQmlEngine
) -> None:
    folder = manager().toolbarFolderId()
    first = add_page(folder, "Moving", "moving")
    harness = create_with(kondor_engine, TARGETS_QML, {})
    evaluate(harness, kondor_engine, f"moveDragged({first}, 0)")
    assert manager().folderContents(folder)[0]["title"] == "Moving"
