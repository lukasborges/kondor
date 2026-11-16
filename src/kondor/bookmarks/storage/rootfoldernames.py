from PySide6.QtCore import QCoreApplication

CONTEXT = "BookmarksPanelEntries"


def translated_root_name(special: str) -> str:
    if special == "toolbar":
        return str(QCoreApplication.translate(CONTEXT, "Bookmarks Toolbar"))
    if special == "other":
        return str(QCoreApplication.translate(CONTEXT, "Other Bookmarks"))
    return ""


def display_title(special: str, stored_title: str) -> str:
    return translated_root_name(special) or stored_title
