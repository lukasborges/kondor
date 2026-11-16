from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlComponent, QQmlEngine

from tests.qmlsupport import error_text, load_component

KEPT_COMPONENTS: list[QQmlComponent] = []


def create_kept(engine: QQmlEngine, source: str) -> QObject:
    component = load_component(engine, source)
    created = component.create()
    assert created is not None, error_text(component)
    QQmlEngine.setObjectOwnership(created, QQmlEngine.ObjectOwnership.CppOwnership)
    KEPT_COMPONENTS.append(component)
    return created
