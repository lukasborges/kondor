from typing import Any

from PySide6.QtCore import Property, QAbstractItemModel, QObject, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication

from kondor.bookmarks import bookmarkedits
from kondor.bookmarks.bookmarkmodel import BookmarkModel
from kondor.bookmarks.bookmarkrow import BookmarkRow
from kondor.bookmarks.htmlimport.bookmarkhtmlimporter import import_bookmarks
from kondor.bookmarks.htmlimport.bookmarkhtmlparser import parse
from kondor.bookmarks.storage import bookmarkfolderlist, bookmarkqueries
from kondor.bookmarks.storage.bookmarkfoldertree import insert_row

DEFAULT_SEARCH_LIMIT = 4


class BookmarkManager(QObject):
    bookmarksChanged = Signal()
    _instance: "BookmarkManager | None" = None

    def __init__(self) -> None:
        super().__init__()
        self._revision = 0
        self._folder_models: dict[int, BookmarkModel] = {}
        self._toolbar_model = BookmarkModel(self)
        self._toolbar_model.set_folder_id(self.toolbarFolderId())

    @classmethod
    def instance(cls) -> "BookmarkManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def toolbar_model(self) -> BookmarkModel:
        return self._toolbar_model

    def folder_list(self) -> list[dict[str, Any]]:
        return bookmarkfolderlist.folders()

    def current_revision(self) -> int:
        return self._revision

    toolbarModel = Property(QAbstractItemModel, toolbar_model, constant=True)
    folders = Property("QVariantList", folder_list, notify=bookmarksChanged)
    revision = Property(int, current_revision, notify=bookmarksChanged)

    @Slot(QUrl, result=bool)
    def isBookmarked(self, url: QUrl) -> bool:
        return bookmarkqueries.is_bookmarked(url)

    @Slot(str, result="QVariantList")
    @Slot(str, int, result="QVariantList")
    def search(self, text: str, limit: int = DEFAULT_SEARCH_LIMIT) -> list[dict[str, Any]]:
        return bookmarkqueries.search(text, limit)

    @Slot(QUrl, result="qint64")
    def bookmarkIdFor(self, url: QUrl) -> int:
        return bookmarkqueries.bookmark_id_for(url)

    @Slot(QUrl, str, "qint64", result="qint64")
    def addBookmark(self, url: QUrl, title: str, folder_id: int) -> int:
        return self._insert_row_and_notify(bookmarkedits.new_bookmark_row(url, title, folder_id))

    @Slot(str, "qint64", result="qint64")
    def addFolder(self, title: str, parent_id: int) -> int:
        return self._insert_row_and_notify(bookmarkedits.new_folder_row(title, parent_id))

    @Slot("qint64", str)
    def rename(self, row_id: int, title: str) -> None:
        self._notify_when(bookmarkedits.rename_row(row_id, title))

    @Slot("qint64", QUrl)
    def setUrl(self, row_id: int, url: QUrl) -> None:
        self._notify_when(bookmarkedits.set_row_url(row_id, url))

    @Slot("qint64", "qint64", int)
    def move(self, row_id: int, new_parent_id: int, new_position: int) -> None:
        self._notify_when(bookmarkedits.move_row(row_id, new_parent_id, new_position))

    @Slot("qint64")
    def remove(self, row_id: int) -> None:
        self._notify_when(bookmarkedits.remove_row(row_id))

    @Slot(QUrl, result=int)
    def importHtml(self, file_url: QUrl) -> int:
        imported = import_bookmarks(parse(bookmarkedits.read_utf8_file(file_url)))
        self._notify_when(imported > 0)
        return imported

    @Slot(result="qint64")
    def toolbarFolderId(self) -> int:
        return bookmarkqueries.special_folder_id("toolbar")

    @Slot(result="qint64")
    def otherFolderId(self) -> int:
        return bookmarkqueries.special_folder_id("other")

    @Slot("qint64", result=BookmarkModel)
    def modelForFolder(self, folder_id: int) -> BookmarkModel:
        if folder_id == self.toolbarFolderId():
            return self._toolbar_model
        if folder_id not in self._folder_models:
            self._folder_models[folder_id] = self._new_folder_model(folder_id)
        return self._folder_models[folder_id]

    @Slot("qint64", result="QVariantList")
    def folderContents(self, folder_id: int) -> list[dict[str, Any]]:
        return bookmarkqueries.folder_contents(folder_id)

    @Slot("qint64", result="QVariantMap")
    def bookmark(self, row_id: int) -> dict[str, Any]:
        return bookmarkqueries.bookmark(row_id)

    @Slot("qint64", result=int)
    def childCount(self, folder_id: int) -> int:
        return bookmarkqueries.child_count(folder_id)

    @Slot(result=bool)
    def ctrlPressed(self) -> bool:
        modifiers = QGuiApplication.queryKeyboardModifiers()
        return bool(modifiers & Qt.KeyboardModifier.ControlModifier)

    def _new_folder_model(self, folder_id: int) -> BookmarkModel:
        model = BookmarkModel(self)
        model.set_folder_id(folder_id)
        return model

    def _insert_row_and_notify(self, row: BookmarkRow | None) -> int:
        row_id = insert_row(row) if row is not None else -1
        self._notify_when(row_id > 0)
        return row_id

    def _notify_when(self, has_changed: bool) -> None:
        if has_changed:
            self._notify_changed()

    def _notify_changed(self) -> None:
        self._revision += 1
        self._toolbar_model.set_folder_id(self.toolbarFolderId())
        self._toolbar_model.refresh()
        for model in self._folder_models.values():
            model.refresh()
        self.bookmarksChanged.emit()
