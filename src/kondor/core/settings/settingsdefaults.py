from collections.abc import Callable

from PySide6.QtCore import QLocale, QStandardPaths

from kondor.core.settings import spellcheckdictionaries

FALLBACK_SPELL_CHECK_LANGUAGE = "en-US"


def system_spell_check_languages() -> list[str]:
    system = QLocale.system().name().replace("_", "-")
    if system in spellcheckdictionaries.dictionary_codes():
        return [system]
    return [FALLBACK_SPELL_CHECK_LANGUAGE]


def default_download_directory() -> str:
    return str(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation))


def constant(value: object) -> Callable[[], object]:
    return lambda: value


def empty_list() -> list[str]:
    return []


FACTORIES: dict[str, Callable[[], object]] = {
    "homePage": constant(""),
    "searchEngine": constant("duckduckgo"),
    "customSearchUrl": constant(""),
    "downloadDirectory": default_download_directory,
    "askWhereToSave": constant(False),
    "startupBehavior": constant("homepage"),
    "showBookmarksBar": constant(False),
    "sideBarCollapsed": constant(False),
    "showTopSites": constant(True),
    "hiddenTopSites": empty_list,
    "clearDataOnExit": constant(False),
    "blockThirdPartyCookies": constant(False),
    "searchSuggestions": constant(False),
    "tabStyle": constant("floating"),
    "readerFontSize": constant(18),
    "readerSerif": constant(True),
    "spellCheckEnabled": constant(True),
    "spellCheckLanguages": system_spell_check_languages,
    "adBlockEnabled": constant(True),
    "adBlockAllowList": empty_list,
    "offerToSavePasswords": constant(True),
    "passwordNeverSaveSites": empty_list,
    "extensionsAutoUpdate": constant(True),
    "pinnedExtensions": empty_list,
    "remoteControlEnabled": constant(False),
    "remoteControlPort": constant(9222),
}


def value_for(name: str) -> object:
    factory = FACTORIES.get(name)
    return factory() if factory is not None else None
