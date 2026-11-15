from pathlib import Path

from PySide6.QtCore import QObject, Qt, QUrl
from PySide6.QtGui import QGuiApplication
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


MINE = {"First", "Second", "Third"}


def toolbar_titles() -> list[str]:
    entries = manager().folderContents(manager().toolbarFolderId())
    return [entry["title"] for entry in entries if entry["title"] in MINE]


def add_three_bookmarks() -> list[int]:
    folder = manager().toolbarFolderId()
    return [add_page(folder, name, name.lower()) for name in ("First", "Second", "Third")]


def test_dragging_an_item_to_a_later_position_moves_it_there(
    fresh_bookmarks: Path, kondor_engine: QQmlEngine
) -> None:
    first = add_three_bookmarks()[0]
    base = toolbar_count() - 3
    harness = create_with(kondor_engine, TARGETS_QML, {})
    evaluate(harness, kondor_engine, f"moveDragged({first}, {base + 2})")
    assert toolbar_titles() == ["Second", "First", "Third"]


def test_dragging_an_item_to_an_earlier_position_moves_it_there(
    fresh_bookmarks: Path, kondor_engine: QQmlEngine
) -> None:
    third = add_three_bookmarks()[2]
    base = toolbar_count() - 3
    harness = create_with(kondor_engine, TARGETS_QML, {})
    evaluate(harness, kondor_engine, f"moveDragged({third}, {base + 1})")
    assert toolbar_titles() == ["First", "Third", "Second"]


def test_dropped_link_takes_its_title_from_the_html_text(
    fresh_bookmarks: Path, kondor_engine: QQmlEngine
) -> None:
    harness = create_with(kondor_engine, TARGETS_QML, {})
    html = "<a href='https://a.example/'>Fish &amp; <b>Chips</b></a>"
    script = (
        "titleOfDrop({ hasText: true, text: 'https://a.example/', hasUrls: true,"
        f" urls: ['https://a.example/'], hasHtml: true, html: \"{html}\" }})"
    )
    assert evaluate(harness, kondor_engine, script) == "Fish & Chips"


def test_dropped_plain_url_is_its_own_title(
    fresh_bookmarks: Path, kondor_engine: QQmlEngine
) -> None:
    harness = create_with(kondor_engine, TARGETS_QML, {})
    script = (
        "titleOfDrop({ hasText: true, text: 'https://a.example/', hasUrls: false, hasHtml: false })"
    )
    assert evaluate(harness, kondor_engine, script) == "https://a.example/"


def test_right_to_left_puts_the_overflow_button_before_the_first_item(
    fresh_bookmarks: Path, kondor_engine: QQmlEngine, tabs: TabModel
) -> None:
    fill_toolbar(12)
    QGuiApplication.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    try:
        bar = create_bar(kondor_engine, tabs, 400)
        count_visible(bar, kondor_engine)
        overflow = bar.findChild(QObject, "overflowButton")
        assert overflow.property("x") < bar.property("width") / 2
    finally:
        QGuiApplication.setLayoutDirection(Qt.LayoutDirection.LeftToRight)


def test_a_private_window_offers_no_add_action(
    fresh_bookmarks: Path, kondor_engine: QQmlEngine, tabs: TabModel
) -> None:
    tabs.addTab(True, QUrl("https://private.example/"))
    bar = create_bar(kondor_engine, tabs, 400)
    actions = bar.findChild(QObject, "actions")
    link_drop = bar.findChild(QObject, "linkDrop")
    assert actions.property("canAddBookmarks") is False
    assert link_drop.property("enabled") is False
