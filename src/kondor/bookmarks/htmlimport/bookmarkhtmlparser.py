import re
from dataclasses import dataclass, field

from PySide6.QtCore import QUrl

from kondor.bookmarks.bookmarkrow import is_supported_bookmark_url
from kondor.bookmarks.htmlimport.bookmarkhtmltext import attribute_value, clean_title

FOLDER_TITLE_END = re.compile(r"</h3", re.IGNORECASE)
LINK_TEXT_END = re.compile(r"</a", re.IGNORECASE)
TAG_NAME = re.compile(r"[^\s/]*")
COMMENT_START = "<!--"
COMMENT_END = "-->"


@dataclass
class ImportedBookmark:
    is_folder: bool = False
    title: str = ""
    url: QUrl = field(default_factory=QUrl)
    children: list["ImportedBookmark"] = field(default_factory=list)


@dataclass
class ParsedBookmarks:
    root: ImportedBookmark
    bookmark_count: int


@dataclass(frozen=True)
class Tag:
    name: str
    text: str
    is_closing: bool


def tag_name(text: str) -> str:
    match = TAG_NAME.match(text)
    return match.group(0).lower() if match is not None else ""


def parse_tag(raw: str) -> Tag:
    text = raw.strip()
    is_closing = text.startswith("/")
    if is_closing:
        text = text[1:].strip()
    return Tag(tag_name(text), text, is_closing)


class Scanner:
    def __init__(self, html: str) -> None:
        self._html = html
        self._position = 0
        self._count = 0
        self._root = ImportedBookmark(is_folder=True)
        self._stack = [self._root]
        self._pending: ImportedBookmark | None = None

    def scan(self) -> ParsedBookmarks:
        while self._position < len(self._html) and self._scan_next():
            pass
        return ParsedBookmarks(self._root, self._count)

    def _scan_next(self) -> bool:
        open_index = self._html.find("<", self._position)
        if open_index < 0:
            return False
        if self._html.startswith(COMMENT_START, open_index):
            return self._skip_comment(open_index)
        return self._read_tag(open_index)

    def _skip_comment(self, open_index: int) -> bool:
        end = self._html.find(COMMENT_END, open_index + len(COMMENT_START))
        self._position = len(self._html) if end < 0 else end + len(COMMENT_END)
        return True

    def _read_tag(self, open_index: int) -> bool:
        close = self._html.find(">", open_index)
        if close < 0:
            return False
        self._position = close + 1
        return self._handle(parse_tag(self._html[open_index + 1 : close]))

    def _handle(self, tag: Tag) -> bool:
        if tag.name == "h3":
            return self._read_folder_title()
        if tag.name == "dl":
            return self._change_list(tag.is_closing)
        if tag.name == "a" and not tag.is_closing:
            return self._read_link(tag.text)
        return True

    def _read_folder_title(self) -> bool:
        close = self._end_of_text(FOLDER_TITLE_END)
        if close < 0:
            return False
        title = clean_title(self._html[self._position : close])
        self._pending = self._add_child(ImportedBookmark(is_folder=True, title=title))
        self._skip_past_tag_end(close)
        return True

    def _change_list(self, is_closing: bool) -> bool:
        if is_closing and len(self._stack) > 1:
            self._stack.pop()
        if not is_closing:
            self._stack.append(self._pending if self._pending is not None else self._stack[-1])
        self._pending = None
        return True

    def _read_link(self, tag_text: str) -> bool:
        close = self._end_of_text(LINK_TEXT_END)
        if close < 0:
            return False
        url = QUrl(attribute_value(tag_text, "href").strip())
        if is_supported_bookmark_url(url):
            self._add_link(url, clean_title(self._html[self._position : close]))
        self._skip_past_tag_end(close)
        return True

    def _add_link(self, url: QUrl, title: str) -> None:
        self._add_child(ImportedBookmark(title=title or url.toString(), url=url))
        self._count += 1

    def _end_of_text(self, closing_tag: re.Pattern[str]) -> int:
        match = closing_tag.search(self._html, self._position)
        return -1 if match is None else match.start()

    def _skip_past_tag_end(self, start: int) -> None:
        after = self._html.find(">", start)
        self._position = len(self._html) if after < 0 else after + 1

    def _add_child(self, child: ImportedBookmark) -> ImportedBookmark:
        self._stack[-1].children.append(child)
        return child


def parse(html: str) -> ParsedBookmarks:
    return Scanner(html).scan()
