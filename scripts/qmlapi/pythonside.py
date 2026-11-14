import importlib.util
from pathlib import Path

from PySide6.QtCore import QMetaMethod, QMetaObject, QObject

from .model import ClassApi, Property, add_counts


def own_properties(meta: QMetaObject) -> dict[str, Property]:
    properties = {}
    for index in range(QObject.staticMetaObject.propertyCount(), meta.propertyCount()):
        item = meta.property(index)
        properties[item.name()] = Property(item.typeName(), item.isWritable())
    return properties


def add_method(api: ClassApi, method: QMetaMethod) -> None:
    name = bytes(method.name().data()).decode()
    target = api.signals if method.methodType() == QMetaMethod.MethodType.Signal else api.callables
    add_counts(target, name, {method.parameterCount()})


def describe_class(meta: QMetaObject) -> ClassApi:
    api = ClassApi(meta.className(), own_properties(meta))
    for index in range(QObject.staticMetaObject.methodCount(), meta.methodCount()):
        add_method(api, meta.method(index))
    return api


def load_qml_types(path: Path) -> tuple:
    spec = importlib.util.spec_from_file_location(f"qmltypes_{path.parent.name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.QML_TYPES


def python_classes(repository: Path) -> dict[str, ClassApi]:
    classes = {}
    for path in sorted((repository / "kondor").rglob("qmltypes.py")):
        for entry in load_qml_types(path):
            api = describe_class(entry.type_class.staticMetaObject())
            classes[api.name] = api
    return classes
