from collections.abc import Callable
from typing import NamedTuple

from PySide6.QtCore import QDateTime, QTimeZone

from kondor.core.settings.settingsdefaults import default_download_directory


class StorageRow(NamedTuple):
    name: str
    key: str
    value: object


TEXT = "changed"
LIST = ["a.example"]
LAST_UPDATE = QDateTime.fromSecsSinceEpoch(1000000, QTimeZone(QTimeZone.Initialization.UTC))

STORAGE_ROWS = (
    StorageRow("homePage", "General/HomePage", TEXT),
    StorageRow("searchEngine", "Search/Engine", TEXT),
    StorageRow("customSearchUrl", "Search/CustomUrl", TEXT),
    StorageRow("downloadDirectory", "Downloads/Directory", TEXT),
    StorageRow("askWhereToSave", "Downloads/AskWhereToSave", True),
    StorageRow("startupBehavior", "General/Startup", TEXT),
    StorageRow("showBookmarksBar", "UI/ShowBookmarksBar", True),
    StorageRow("showTopSites", "NewTab/ShowTopSites", False),
    StorageRow("hiddenTopSites", "NewTab/HiddenTopSites", LIST),
    StorageRow("clearDataOnExit", "Privacy/ClearOnExit", True),
    StorageRow("blockThirdPartyCookies", "Privacy/BlockThirdPartyCookies", True),
    StorageRow("searchSuggestions", "Search/Suggestions", True),
    StorageRow("spellCheckEnabled", "SpellCheck/Enabled", False),
    StorageRow("spellCheckLanguages", "SpellCheck/Languages", LIST),
    StorageRow("tabStyle", "UI/TabStyle", "classic"),
    StorageRow("readerFontSize", "Reader/FontSize", 24),
    StorageRow("readerSerif", "Reader/Serif", False),
    StorageRow("adBlockLastUpdate", "AdBlock/LastUpdate", LAST_UPDATE),
    StorageRow("adBlockEnabled", "AdBlock/Enabled", False),
    StorageRow("adBlockAllowList", "AdBlock/AllowList", LIST),
    StorageRow("offerToSavePasswords", "Passwords/OfferToSave", False),
    StorageRow("passwordNeverSaveSites", "Passwords/NeverSave", LIST),
    StorageRow("extensionsAutoUpdate", "Extensions/AutoUpdate", False),
    StorageRow("pinnedExtensions", "Extensions/Pinned", LIST),
)
STRING_LIST_NAMES = tuple(row.name for row in STORAGE_ROWS if row.value is LIST)

DEFAULT_ROWS: tuple[tuple[str, object | Callable[[], object]], ...] = (
    ("homePage", ""),
    ("searchEngine", "duckduckgo"),
    ("customSearchUrl", ""),
    ("downloadDirectory", default_download_directory),
    ("askWhereToSave", False),
    ("startupBehavior", "homepage"),
    ("showBookmarksBar", False),
    ("tabStyle", "floating"),
    ("showTopSites", True),
    ("hiddenTopSites", []),
    ("clearDataOnExit", False),
    ("blockThirdPartyCookies", False),
    ("searchSuggestions", False),
    ("spellCheckEnabled", True),
    ("offerToSavePasswords", True),
    ("passwordNeverSaveSites", []),
    ("pinnedExtensions", []),
    ("spellCheckLanguages", ["en-US"]),
)
DEFAULT_NAMES = tuple(name for name, _ in DEFAULT_ROWS)
