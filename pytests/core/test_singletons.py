import pytest
from PySide6.QtQml import QQmlEngine

from kondor.core.qmlregistration import QmlType
from pytests.kondortypes import singleton_types

SINGLETONS = singleton_types()


@pytest.mark.parametrize("entry", SINGLETONS, ids=[entry.name for entry in SINGLETONS])
def test_qml_singleton_is_the_class_instance(
    entry: QmlType, kondor_engine: QQmlEngine
) -> None:
    singleton = kondor_engine.singletonInstance("Kondor", entry.name)
    assert singleton is entry.type_class.instance()
