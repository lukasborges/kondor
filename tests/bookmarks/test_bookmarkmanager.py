from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlEngine
from pytestqt.qtbot import QtBot

from tests.bookmarks.bookmarkrows import add_folder_in_other, add_page, manager
from tests.qmlsupport import captured_messages, error_text, load_component

DEFAULT_TOOLBAR_SIZE = 6

WIDE_ID_QML = """
import QtQml
import Kondor

QtObject {
    property int wideIdChildren: BookmarkManager.childCount(4294967296
                                                            + BookmarkManager.toolbarFolderId())
    property int toolbarChildren: BookmarkManager.childCount(BookmarkManager.toolbarFolderId())
    property int kdeMatches: BookmarkManager.search("kde").length
}
"""


def test_add_bookmark_refuses_unsupported_schemes(fresh_bookmarks: Path) -> None:
    other = manager().otherFolderId()
    assert manager().addBookmark(QUrl("place:type=6"), "Place", other) == -1
    assert manager().addBookmark(QUrl("javascript:alert(1)"), "Script", other) == -1


def test_add_bookmark_falls_back_to_other_bookmarks(fresh_bookmarks: Path) -> None:
    page = add_page(manager().toolbarFolderId(), "Page", "page")
    into_page = manager().addBookmark(QUrl("https://kde.org/a"), "A", page)
    into_nothing = manager().addBookmark(QUrl("https://kde.org/b"), "B", 0)
    assert manager().bookmark(into_page)["parentId"] == manager().otherFolderId()
    assert manager().bookmark(into_nothing)["parentId"] == manager().otherFolderId()


def test_add_folder_names_a_blank_title_new_folder(fresh_bookmarks: Path) -> None:
    folder = add_folder_in_other("   ")
    assert manager().bookmark(folder)["title"] == "New Folder"


def test_rename_ignores_a_blank_title(fresh_bookmarks: Path) -> None:
    folder = add_folder_in_other("Kept")
    manager().rename(folder, "  ")
    assert manager().bookmark(folder)["title"] == "Kept"


def test_set_url_ignores_folders(fresh_bookmarks: Path) -> None:
    folder = add_folder_in_other("Folder")
    manager().setUrl(folder, QUrl("https://kde.org/"))
    assert manager().bookmark(folder)["url"] == ""


def test_remove_refuses_special_folders(fresh_bookmarks: Path) -> None:
    other = manager().otherFolderId()
    manager().remove(other)
    assert manager().bookmark(other)["special"] == "other"


def test_changes_bump_revision_and_emit_once(fresh_bookmarks: Path, qtbot: QtBot) -> None:
    emitted: list[None] = []
    revision = manager().revision
    manager().bookmarksChanged.connect(lambda: emitted.append(None))
    add_page(manager().otherFolderId(), "Page", "page")
    manager().bookmarksChanged.disconnect()
    assert len(emitted) == 1
    assert manager().revision == revision + 1
    with qtbot.assertNotEmitted(manager().bookmarksChanged):
        manager().rename(manager().otherFolderId() + 1000, "Missing")


def test_import_of_a_missing_file_imports_nothing(fresh_bookmarks: Path, tmp_path: Path) -> None:
    missing = QUrl.fromLocalFile(str(tmp_path / "missing.html"))
    assert manager().importHtml(missing) == 0
    titles = [row["title"] for row in manager().folderContents(manager().otherFolderId())]
    assert "Imported" not in titles


def test_ids_from_qml_are_64_bit(fresh_bookmarks: Path, kondor_engine: QQmlEngine) -> None:
    component = load_component(kondor_engine, WIDE_ID_QML)
    with captured_messages() as messages:
        created = component.create()
    assert created is not None, error_text(component)
    assert messages == []
    assert created.property("toolbarChildren") == DEFAULT_TOOLBAR_SIZE
    assert created.property("wideIdChildren") == 0
    assert created.property("kdeMatches") > 0


def test_recent_bookmarks_lists_the_newest_first_and_skips_folders(fresh_bookmarks: Path) -> None:
    other = manager().otherFolderId()
    add_page(other, "First", "first")
    add_folder_in_other("Folder")
    add_page(other, "Second", "second")
    add_page(other, "Third", "third")
    titles = [row["title"] for row in manager().recentBookmarks(2)]
    assert titles == ["Third", "Second"]


def test_recent_bookmarks_of_a_non_positive_limit_is_empty(fresh_bookmarks: Path) -> None:
    add_page(manager().otherFolderId(), "Page", "page")
    assert manager().recentBookmarks(0) == []
