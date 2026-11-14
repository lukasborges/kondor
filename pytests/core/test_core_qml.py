from PySide6.QtQml import QQmlEngine

from pytests.qmlsupport import captured_messages, error_text, load_component

SOURCE = """import QtQml
import Kondor

QtObject {
    property string engine: Settings.searchEngine
    property string name: FileHelper.sanitizeFileName("a/b")
}
"""


def test_core_singletons_are_read_from_qml(kondor_engine: QQmlEngine) -> None:
    component = load_component(kondor_engine, SOURCE)
    with captured_messages() as messages:
        created = component.create()
    assert created is not None, error_text(component)
    assert messages == []
    assert created.property("engine") == "duckduckgo"
    assert created.property("name") == "a_b"
