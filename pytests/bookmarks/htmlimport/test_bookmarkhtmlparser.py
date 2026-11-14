from PySide6.QtCore import QUrl

from kondor.bookmarks.htmlimport.bookmarkhtmlparser import parse

NESTED_FOLDERS = (
    "<DL><p><DT><H3>Outer</H3><DL><p>"
    '<DT><A HREF="https://kde.org/">KDE</A>'
    '<DT><H3>Inner</H3><DL><p><DT><A HREF="https://qt.io/">Qt</A></DL><p>'
    '</DL><p><DT><A HREF="https://example.org/">Top</A></DL><p>'
)
COMMENTS_AND_SCHEMES = (
    '<DL><!-- <A HREF="https://hidden.example/">Hidden</A> -->'
    '<DT><A HREF="place:type=6">Place</A>'
    '<DT><A HREF="javascript:alert(1)">Script</A>'
    '<DT><A HREF="https://kde.org/">KDE</A></DL>'
)
ENTITIES = (
    '<DL><DT><A HREF="https://kde.org/">KDE &amp; Qt &#128512; &#x1F600; &#0; <b>bold</b></A></DL>'
)
NESTED_BOOKMARK_COUNT = 3
TWO_CHILDREN = 2


def test_parses_nested_folders() -> None:
    parsed = parse(NESTED_FOLDERS)
    assert parsed.bookmark_count == NESTED_BOOKMARK_COUNT
    assert len(parsed.root.children) == TWO_CHILDREN
    outer = parsed.root.children[0]
    assert outer.is_folder
    assert outer.title == "Outer"
    assert len(outer.children) == TWO_CHILDREN
    assert outer.children[1].children[0].title == "Qt"
    assert parsed.root.children[1].title == "Top"


def test_skips_comments_and_unsupported_schemes() -> None:
    parsed = parse(COMMENTS_AND_SCHEMES)
    assert parsed.bookmark_count == 1
    assert len(parsed.root.children) == 1
    assert parsed.root.children[0].url == QUrl("https://kde.org/")


def test_decodes_entities_in_titles() -> None:
    parsed = parse(ENTITIES)
    assert len(parsed.root.children) == 1
    assert parsed.root.children[0].title == "KDE & Qt \U0001f600 \U0001f600 &#0; bold"


def test_uses_url_when_title_is_empty() -> None:
    parsed = parse('<DL><DT><A HREF="https://kde.org/">  </A></DL>')
    assert len(parsed.root.children) == 1
    assert parsed.root.children[0].title == "https://kde.org/"
