import re
from html import escape

from PySide6.QtCore import QUrl

SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)


def address_without_scheme(url: QUrl) -> str:
    text = SCHEME.sub("", url.toString())
    return text[:-1] if text.endswith("/") and text.count("/") == 1 else text


def query_words(query: str) -> list[str]:
    return query.casefold().split()


def matches_all_words(text: str, words: list[str]) -> bool:
    folded = text.casefold()
    return all(word in folded for word in words)


def match_spans(text: str, words: list[str]) -> list[tuple[int, int]]:
    folded = text.casefold()
    found = [(m.start(), m.end()) for word in words for m in re.finditer(re.escape(word), folded)]
    return merge_spans(sorted(found))


def merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def highlight(text: str, words: list[str]) -> str:
    parts: list[str] = []
    position = 0
    for start, end in match_spans(text, words):
        parts += [escape(text[position:start]), "<b>", escape(text[start:end]), "</b>"]
        position = end
    return "".join(parts) + escape(text[position:])
