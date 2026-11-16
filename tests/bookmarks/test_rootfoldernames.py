import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QTranslator

from tests.bookmarks.bookmarkrows import manager

I18N_DIR = Path(__file__).resolve().parents[2] / "i18n"


@pytest.fixture
def german_translator(tmp_path: Path) -> Iterator[None]:
    compiled = tmp_path / "kondor_de.qm"
    subprocess.run(
        ["pyside6-lrelease", str(I18N_DIR / "kondor_de.ts"), "-qm", str(compiled)],
        check=True,
        capture_output=True,
    )
    translator = QTranslator()
    assert translator.load(str(compiled))
    QCoreApplication.installTranslator(translator)
    yield
    QCoreApplication.removeTranslator(translator)


def root_titles() -> list[str]:
    folders = manager().folder_list()
    return [folder["title"] for folder in folders if folder["depth"] == 0]


def test_root_folders_are_listed_with_english_names(fresh_bookmarks: Path) -> None:
    assert root_titles()[:2] == ["Bookmarks Toolbar", "Other Bookmarks"]


def test_root_folders_are_listed_with_translated_names(
    fresh_bookmarks: Path, german_translator: None
) -> None:
    assert root_titles()[:2] == ["Lesezeichen-Symbolleiste", "Weitere Lesezeichen"]
