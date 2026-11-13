from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlEngine

from kondor.core.qmlregistration import QmlKind, QmlType, register
from pytests.qmlsupport import create_object, error_text, load_component


class SingletonProbe(QObject):
    _instance: "SingletonProbe | None" = None

    @classmethod
    def instance(cls) -> "SingletonProbe":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


class CreatableProbe(QObject):
    pass


class UncreatableProbe(QObject):
    pass


def register_probes() -> None:
    register(
        (
            QmlType(SingletonProbe, "SingletonProbe", QmlKind.SINGLETON),
            QmlType(CreatableProbe, "CreatableProbe", QmlKind.CREATABLE),
            QmlType(UncreatableProbe, "UncreatableProbe", QmlKind.UNCREATABLE),
        )
    )


register_probes()


def test_singleton_is_the_instance_of_the_class(qml_engine: QQmlEngine) -> None:
    singleton = qml_engine.singletonInstance("Kondor", "SingletonProbe")
    assert singleton is SingletonProbe.instance()


def test_creatable_type_is_created_from_qml(qml_engine: QQmlEngine) -> None:
    created = create_object(qml_engine, "import Kondor\nCreatableProbe {}")
    assert isinstance(created, CreatableProbe)


def test_uncreatable_type_fails_with_the_reason(qml_engine: QQmlEngine) -> None:
    component = load_component(qml_engine, "import Kondor\nUncreatableProbe {}")
    assert component.create() is None
    assert "UncreatableProbe cannot be created from QML" in error_text(component)
