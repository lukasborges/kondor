from collections.abc import Callable, Sequence
from typing import Any

from PySide6.QtCore import (
    Property,
    QFileInfo,
    QObject,
    Signal,
    SignalInstance,
    Slot,
)

from kondor.core.settings import searchengines, settingsdefaults, spellcheckdictionaries
from kondor.core.settings.settingsoptions import (
    CUSTOM_SEARCH_URL,
    DOWNLOAD_DIRECTORY,
    READER_FONT_SIZE,
    SEARCH_ENGINE,
    STORED_OPTIONS,
    TAB_SLEEP_MINUTES_OPTION,
    TAB_STYLE,
    StoredOption,
)
from kondor.profiles.activeprofile import ActiveProfile

TAB_STYLES = ("floating", "below", "vertical", "classic")
DEFAULT_TAB_STYLE = "floating"
TAB_SLEEP_MINUTES = (15, 30, 60, 120, 240)
DEFAULT_TAB_SLEEP_MINUTES = 30
MIN_READER_FONT_SIZE = 12
MAX_READER_FONT_SIZE = 32


def clamped_reader_font_size(size: Any) -> int:
    return max(MIN_READER_FONT_SIZE, min(int(size), MAX_READER_FONT_SIZE))


def known_tab_style(style: Any) -> str:
    return style if style in TAB_STYLES else DEFAULT_TAB_STYLE


def known_tab_sleep_minutes(minutes: Any) -> int:
    return minutes if minutes in TAB_SLEEP_MINUTES else DEFAULT_TAB_SLEEP_MINUTES


def normalized(option: StoredOption, value: Any) -> Any:
    if option is TAB_STYLE:
        return known_tab_style(value)
    if option is TAB_SLEEP_MINUTES_OPTION:
        return known_tab_sleep_minutes(value)
    if option is READER_FONT_SIZE:
        return clamped_reader_font_size(value)
    return value


def download_directory(settings: "Settings") -> str:
    if settings.is_download_directory_valid():
        return str(settings.stored_value(DOWNLOAD_DIRECTORY))
    return settingsdefaults.default_download_directory()


def stored_getter(option: StoredOption) -> Callable[["Settings"], Any]:
    if option is DOWNLOAD_DIRECTORY:
        return download_directory
    return lambda settings: settings.stored_value(option)


def stored_setter(option: StoredOption) -> Callable[["Settings", Any], None]:
    return lambda settings, value: settings.store(option, value)


def stored_members(options: Sequence[StoredOption]) -> dict[str, Any]:
    members: dict[str, Any] = {}
    for option in options:
        changed = Signal()
        getter, setter = stored_getter(option), stored_setter(option)
        members[option.changed] = changed
        members[option.name] = Property(option.property_type, getter, setter, notify=changed)
    return members


STORED_MEMBERS = stored_members(STORED_OPTIONS)


class Settings(QObject):
    vars().update(STORED_MEMBERS)
    _instance: "Settings | None" = None

    def __init__(self) -> None:
        super().__init__()
        self._storage = ActiveProfile.settings()
        self._values = {option.name: self.read(option) for option in STORED_OPTIONS}

    @classmethod
    def instance(cls) -> "Settings":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def read(self, option: StoredOption) -> Any:
        fallback = settingsdefaults.value_for(option.name)
        value = self._storage.value(option.key, fallback, type=option.read_type)
        return normalized(option, option.read_type() if value is None else value)

    def stored_value(self, option: StoredOption) -> Any:
        return self._values[option.name]

    def store(self, option: StoredOption, value: Any) -> None:
        value = normalized(option, value)
        if self._values[option.name] == value:
            return
        self._values[option.name] = value
        self._storage.setValue(option.key, value)
        self._storage.sync()
        self.changed_signal(option).emit()

    def changed_signal(self, option: StoredOption) -> SignalInstance:
        signal: SignalInstance = getattr(self, option.changed)
        return signal

    def is_download_directory_valid(self) -> bool:
        return bool(QFileInfo(self.stored_value(DOWNLOAD_DIRECTORY)).isDir())

    downloadDirectoryValid = Property(
        bool, is_download_directory_valid, notify=STORED_MEMBERS[DOWNLOAD_DIRECTORY.changed]
    )

    @Slot(str, result="QVariant")
    def defaultValue(self, name: str) -> object:
        return settingsdefaults.value_for(name)

    @Slot(result="QVariantList")
    def availableSpellCheckLanguages(self) -> list[dict[str, str]]:
        return spellcheckdictionaries.available_languages()

    @Slot(result=str)
    def searchUrlTemplate(self) -> str:
        return searchengines.url_template(*self.search_settings())

    @Slot(result=str)
    def searchEngineName(self) -> str:
        return searchengines.display_name(*self.search_settings())

    @Slot()
    def refreshDownloadDirectory(self) -> None:
        self.changed_signal(DOWNLOAD_DIRECTORY).emit()

    def search_settings(self) -> tuple[str, str]:
        return self.stored_value(SEARCH_ENGINE), self.stored_value(CUSTOM_SEARCH_URL)
