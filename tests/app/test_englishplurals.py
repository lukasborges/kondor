import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QTranslator

I18N_DIR = Path(__file__).resolve().parents[2] / "i18n"
SOURCE = "%n minute(s)"


@pytest.fixture
def english_translator(qapp: object, tmp_path: Path) -> Iterator[None]:
    compiled = tmp_path / "kondor_en.qm"
    subprocess.run(
        ["pyside6-lrelease", str(I18N_DIR / "kondor_en.ts"), "-qm", str(compiled)],
        check=True,
        capture_output=True,
    )
    translator = QTranslator()
    assert translator.load(str(compiled))
    QCoreApplication.installTranslator(translator)
    yield
    QCoreApplication.removeTranslator(translator)


def minutes(count: int) -> str:
    return QCoreApplication.translate("GeneralPerformanceTab", SOURCE, "", count)


@pytest.mark.usefixtures("english_translator")
def test_uses_the_singular_form_for_one() -> None:
    assert minutes(1) == "1 minute"


@pytest.mark.usefixtures("english_translator")
def test_uses_the_plural_form_for_many() -> None:
    assert minutes(15) == "15 minutes"
