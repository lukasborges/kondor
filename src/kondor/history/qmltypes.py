from kondor.core.qmlregistration import QmlKind, QmlType, register
from kondor.history.historymanager import HistoryManager
from kondor.history.historymodel import HistoryModel

QML_TYPES: tuple[QmlType, ...] = (
    QmlType(HistoryManager, "HistoryManager", QmlKind.SINGLETON),
    QmlType(HistoryModel, "HistoryModel", QmlKind.UNCREATABLE),
)


def register_types() -> None:
    register(QML_TYPES)
