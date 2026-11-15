from collections.abc import Callable
from pathlib import Path
from typing import Any

from kondor.bookmarks.bookmarkmanager import BookmarkManager

SAMPLE_BOOKMARKS_HTML = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 ADD_DATE="1">Bookmarks Toolbar</H3>
    <DL><p>
        <DT><A HREF="https://kde.org/" ADD_DATE="1">KDE &amp; Qt</A>
        <DT><H3 ADD_DATE="1">Nested</H3>
        <DL><p>
            <DT><A HREF="https://planet.kde.org/">Planet KDE</A>
        </DL><p>
    </DL><p>
    <DT><A HREF="https://bookmarks.example/emoji">Emoji &#128512; &#x1F600;</A>
    <DT><A HREF="place:type=6">Unsupported</A>
</DL><p>
"""
FolderRow = dict[str, Any]


def write_sample_export(path: Path) -> None:
    path.write_text(SAMPLE_BOOKMARKS_HTML, encoding="utf-8")


def folder_id_matching(matches: Callable[[FolderRow], bool]) -> int:
    found = (row["id"] for row in BookmarkManager.instance().folders if matches(row))
    return int(next(found, -1))


def imported_folder_id() -> int:
    return folder_id_matching(lambda folder: folder["title"] == "Imported")


def imported_toolbar_id() -> int:
    imported = imported_folder_id()
    return folder_id_matching(
        lambda folder: folder["title"] == "Bookmarks Toolbar" and folder["parentId"] == imported
    )


def nested_folder_id() -> int:
    return folder_id_matching(lambda folder: folder["title"] == "Nested")
