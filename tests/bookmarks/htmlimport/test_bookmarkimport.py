from collections.abc import Iterator
from typing import NamedTuple

import pytest
from PySide6.QtCore import QUrl

from kondor.core.database.database import Database
from tests.bookmarks.bookmarkrows import manager
from tests.bookmarks.conftest import recreate_database
from tests.bookmarks.htmlimport.sampleexport import (
    imported_folder_id,
    imported_toolbar_id,
    nested_folder_id,
    write_sample_export,
)

EMOJI_URL = "https://bookmarks.example/emoji"
IMPORTED_URLS = ("https://kde.org/", "https://planet.kde.org/", EMOJI_URL)


class SampleImport(NamedTuple):
    imported_count: int
    other_children_before: int


@pytest.fixture(scope="module")
def sample_import(
    kondor_types: None, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[SampleImport]:
    recreate_database()
    path = tmp_path_factory.mktemp("import") / "bookmarks.html"
    write_sample_export(path)
    other_children = manager().childCount(manager().toolbarFolderId())
    yield SampleImport(manager().importHtml(QUrl.fromLocalFile(str(path))), other_children)
    Database.reset_instance()


def test_imports_every_bookmark(sample_import: SampleImport) -> None:
    assert sample_import.imported_count == len(IMPORTED_URLS)
    assert all(manager().isBookmarked(QUrl(url)) for url in IMPORTED_URLS)


def test_rebuilds_the_folder_tree_under_other_bookmarks(sample_import: SampleImport) -> None:
    assert imported_folder_id() > 0
    assert imported_toolbar_id() > 0
    assert nested_folder_id() > 0
    assert manager().bookmark(imported_folder_id())["parentId"] == manager().toolbarFolderId()
    assert manager().bookmark(nested_folder_id())["parentId"] == imported_toolbar_id()


def test_appends_the_imported_folder(sample_import: SampleImport) -> None:
    imported = manager().bookmark(imported_folder_id())
    assert imported["position"] == sample_import.other_children_before


def test_decodes_entities_above_the_basic_plane(sample_import: SampleImport) -> None:
    rows = manager().folderContents(imported_folder_id())
    titles = [row["title"] for row in rows if row["url"] == EMOJI_URL]
    assert titles == ["Emoji \U0001f600 \U0001f600"]
