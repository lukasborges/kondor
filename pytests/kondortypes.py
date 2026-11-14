import importlib
import pkgutil
from types import ModuleType

import kondor
from kondor.core.qmlregistration import QmlKind, QmlType

QMLTYPES_MODULE = "qmltypes"


def is_qmltypes_module(name: str) -> bool:
    return name.rsplit(".", 1)[-1] == QMLTYPES_MODULE


def qmltypes_modules() -> list[ModuleType]:
    names = [info.name for info in pkgutil.walk_packages(kondor.__path__, "kondor.")]
    return [importlib.import_module(name) for name in names if is_qmltypes_module(name)]


def singleton_types() -> list[QmlType]:
    entries = [entry for module in qmltypes_modules() for entry in module.QML_TYPES]
    return [entry for entry in entries if entry.kind is QmlKind.SINGLETON]
