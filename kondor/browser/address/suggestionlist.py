from PySide6.QtCore import QJsonDocument

MAX_SUGGESTIONS = 6
SUGGESTIONS_POSITION = 1


def suggestion_entries(body: bytes) -> list[object]:
    root = QJsonDocument.fromJson(body).toVariant()
    if not isinstance(root, list) or len(root) <= SUGGESTIONS_POSITION:
        return []
    entries = root[SUGGESTIONS_POSITION]
    return list(entries) if isinstance(entries, list) else []


def suggestions_from_json(body: bytes) -> list[str]:
    entries = suggestion_entries(body)
    items = [entry for entry in entries if isinstance(entry, str) and entry]
    return items[:MAX_SUGGESTIONS]
