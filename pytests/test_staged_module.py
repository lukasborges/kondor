from PySide6.QtCore import QFile
from PySide6.QtQml import QQmlEngine

from pytests.qmlsupport import captured_messages, create_object


def test_inline_bar_loads_from_the_staged_module_without_warnings(qml_engine: QQmlEngine) -> None:
    with captured_messages() as messages:
        created = create_object(qml_engine, "import Kondor\nInlineBar {}")
    assert created is not None
    assert messages == []


def test_script_resource_is_registered(staged_resources: None) -> None:
    assert QFile(":/scripts/passwords.js").exists()


def test_translation_resource_is_registered(staged_resources: None) -> None:
    assert QFile(":/i18n/kondor_pt_BR.qm").exists()
