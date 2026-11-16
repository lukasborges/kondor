import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from kondor.core.settings.settings import DEFAULT_TAB_SLEEP_MINUTES, Settings
from kondor.core.settings.settingsdefaults import default_download_directory
from tests.core.settingsrows import (
    DEFAULT_NAMES,
    DEFAULT_ROWS,
    STORAGE_ROWS,
    STRING_LIST_NAMES,
    StorageRow,
)

FIXTURES = Path(__file__).resolve().parent.parent / "data" / "core"
DICTIONARIES_VARIABLE = "QTWEBENGINE_DICTIONARIES_PATH"
MIN_READER_FONT_SIZE = 12
MAX_READER_FONT_SIZE = 32


def cleared_settings_file() -> Path:
    storage = QSettings("KDE", "Kondor")
    storage.clear()
    storage.sync()
    return Path(storage.fileName())


@pytest.fixture
def settings_file(qapp: object) -> Iterator[Path]:
    yield cleared_settings_file()
    cleared_settings_file()


@pytest.fixture
def settings(settings_file: Path) -> Settings:
    return Settings()


def settings_from_fixture(settings_file: Path, fixture_name: str) -> Settings:
    shutil.copyfile(FIXTURES / fixture_name, settings_file)
    return Settings()


@pytest.mark.parametrize(("name", "expected"), DEFAULT_ROWS, ids=DEFAULT_NAMES)
def test_default_value(settings: Settings, name: str, expected: object) -> None:
    value = expected() if callable(expected) else expected
    assert settings.defaultValue(name) == value


@pytest.mark.parametrize("name", DEFAULT_NAMES)
def test_fresh_settings_use_defaults(settings: Settings, name: str) -> None:
    assert settings.property(name) == settings.defaultValue(name)


@pytest.mark.parametrize("row", STORAGE_ROWS, ids=[row.name for row in STORAGE_ROWS])
def test_storage_keys_stay_the_same(settings: Settings, row: StorageRow) -> None:
    assert settings.setProperty(row.name, row.value)
    raw = QSettings("KDE", "Kondor")
    assert raw.value(row.key, None, type=type(row.value)) == row.value


def test_reader_font_size_is_clamped(settings: Settings) -> None:
    settings.setProperty("readerFontSize", 100)
    assert settings.property("readerFontSize") == MAX_READER_FONT_SIZE
    settings.setProperty("readerFontSize", 1)
    assert settings.property("readerFontSize") == MIN_READER_FONT_SIZE


def test_reads_the_file_written_by_cpp(settings_file: Path) -> None:
    settings = settings_from_fixture(settings_file, "Kondor.conf")
    rows = [row for row in STORAGE_ROWS if row.name != "downloadDirectory"]
    assert [settings.property(row.name) for row in rows] == [row.value for row in rows]
    assert settings.property("downloadDirectory") == default_download_directory()
    assert settings.property("downloadDirectoryValid") is False


def test_writes_the_same_file_as_cpp(settings: Settings, settings_file: Path) -> None:
    for row in STORAGE_ROWS:
        settings.setProperty(row.name, row.value)
    expected = (FIXTURES / "Kondor.conf").read_text(encoding="utf-8")
    assert settings_file.read_text(encoding="utf-8").splitlines() == expected.splitlines()


def test_reads_empty_lists_written_by_cpp(settings_file: Path) -> None:
    settings = settings_from_fixture(settings_file, "Kondor-empty-lists.conf")
    assert [settings.property(name) for name in STRING_LIST_NAMES] == [[]] * len(STRING_LIST_NAMES)


def test_lists_spell_check_languages_by_name(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for code in ("pt-BR", "en-US"):
        (tmp_path / f"{code}.bdic").touch()
    monkeypatch.setenv(DICTIONARIES_VARIABLE, str(tmp_path))
    languages = settings.availableSpellCheckLanguages()
    assert [language["code"] for language in languages] == ["en-US", "pt-BR"]
    assert languages[1]["name"] == "Português (Brasil)"


def test_search_url_template_uses_custom_url_only_with_placeholder(settings: Settings) -> None:
    settings.setProperty("searchEngine", "custom")
    settings.setProperty("customSearchUrl", "https://x/?q=%1")
    assert settings.searchUrlTemplate() == "https://x/?q=%1"
    assert settings.searchEngineName() == ""
    settings.setProperty("customSearchUrl", "https://x/")
    assert settings.searchUrlTemplate() == "https://duckduckgo.com/?q=%1"


def test_unknown_tab_style_reads_as_floating(settings: Settings) -> None:
    settings.setProperty("tabStyle", "classic")
    settings.setProperty("tabStyle", "sideways")
    assert settings.property("tabStyle") == "floating"


def test_stored_unknown_tab_style_reads_as_floating(settings_file: Path) -> None:
    raw = QSettings("KDE", "Kondor")
    raw.setValue("UI/TabStyle", "sideways")
    raw.sync()
    assert Settings().property("tabStyle") == "floating"


def test_unknown_tab_sleep_minutes_fall_back_to_default(settings: Settings) -> None:
    settings.setProperty("tabSleepMinutes", 7)
    assert settings.property("tabSleepMinutes") == DEFAULT_TAB_SLEEP_MINUTES
