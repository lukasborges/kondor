from typing import NamedTuple

from PySide6.QtCore import QDateTime

STRING_LIST = "QStringList"


class StoredOption(NamedTuple):
    key: str
    name: str
    property_type: type | str
    read_type: type
    changed: str


def option(key: str, name: str, value_type: type) -> StoredOption:
    return StoredOption(key, name, value_type, value_type, f"{name}Changed")


def string_list_option(key: str, name: str) -> StoredOption:
    return StoredOption(key, name, STRING_LIST, list, f"{name}Changed")


HOME_PAGE = option("General/HomePage", "homePage", str)
SEARCH_ENGINE = option("Search/Engine", "searchEngine", str)
CUSTOM_SEARCH_URL = option("Search/CustomUrl", "customSearchUrl", str)
DOWNLOAD_DIRECTORY = option("Downloads/Directory", "downloadDirectory", str)
READER_FONT_SIZE = option("Reader/FontSize", "readerFontSize", int)

STORED_OPTIONS = (
    HOME_PAGE,
    SEARCH_ENGINE,
    CUSTOM_SEARCH_URL,
    DOWNLOAD_DIRECTORY,
    option("Downloads/AskWhereToSave", "askWhereToSave", bool),
    option("General/Startup", "startupBehavior", str),
    option("UI/ShowBookmarksBar", "showBookmarksBar", bool),
    option("NewTab/ShowTopSites", "showTopSites", bool),
    string_list_option("NewTab/HiddenTopSites", "hiddenTopSites"),
    option("Privacy/ClearOnExit", "clearDataOnExit", bool),
    option("Privacy/BlockThirdPartyCookies", "blockThirdPartyCookies", bool),
    option("Search/Suggestions", "searchSuggestions", bool),
    option("SpellCheck/Enabled", "spellCheckEnabled", bool),
    string_list_option("SpellCheck/Languages", "spellCheckLanguages"),
    READER_FONT_SIZE,
    option("Reader/Serif", "readerSerif", bool),
    option("AdBlock/Enabled", "adBlockEnabled", bool),
    string_list_option("AdBlock/AllowList", "adBlockAllowList"),
    option("AdBlock/LastUpdate", "adBlockLastUpdate", QDateTime),
    option("Passwords/OfferToSave", "offerToSavePasswords", bool),
    string_list_option("Passwords/NeverSave", "passwordNeverSaveSites"),
    option("Extensions/AutoUpdate", "extensionsAutoUpdate", bool),
    string_list_option("Extensions/Pinned", "pinnedExtensions"),
)
