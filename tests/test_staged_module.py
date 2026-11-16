from pathlib import Path

from PySide6.QtCore import QFile
from PySide6.QtQml import QQmlEngine

from scripts.staging.install import install_packaging_files
from tests.qmlsupport import captured_messages, create_object


def test_inline_bar_loads_from_the_staged_module_without_warnings(qml_engine: QQmlEngine) -> None:
    with captured_messages() as messages:
        created = create_object(qml_engine, "import Kondor\nInlineBar {}")
    assert created is not None
    assert messages == []


def test_script_resource_is_registered(staged_resources: None) -> None:
    assert QFile(":/scripts/passwords.js").exists()


def test_translation_resource_is_registered(staged_resources: None) -> None:
    assert QFile(":/i18n/kondor_pt_BR.qm").exists()


def test_install_puts_the_krunner_runner_file_in_dbusplugins(tmp_path: Path) -> None:
    repository = Path(__file__).resolve().parent.parent
    install_packaging_files(repository, tmp_path)

    runner = tmp_path / "share/krunner/dbusplugins/io.github.lukasborges.Kondor.krunner.desktop"
    assert "X-Plasma-API=DBus" in runner.read_text()
