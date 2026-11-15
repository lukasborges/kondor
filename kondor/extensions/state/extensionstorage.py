from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import (
    QT_TRANSLATE_NOOP,
    QCoreApplication,
    QJsonArray,
    QJsonDocument,
    QJsonValue,
)

from kondor.core.database import database, sql

STORAGE_QUOTA = 1024 * 1024
NOT_AVAILABLE = QT_TRANSLATE_NOOP("ExtensionManager", "Storage is not available")
STORAGE_FULL = QT_TRANSLATE_NOOP(
    "ExtensionManager", "The extension's storage is full (limit: 1 MiB)"
)
USED_BYTES = (
    "SELECT COALESCE(SUM(LENGTH(CAST(key AS BLOB)) + LENGTH(CAST(value AS BLOB))), 0) "
    "FROM extension_storage WHERE extension_id = ? AND key != ?"
)
INSERT_VALUE = (
    "INSERT OR REPLACE INTO extension_storage (extension_id, key, value) VALUES (?, ?, ?)"
)


@dataclass
class StorageWrite:
    is_written: bool = False
    error: str = ""


def translated(text: str) -> str:
    return str(QCoreApplication.translate("ExtensionManager", text))


def first_element(json: str) -> Any:
    document = QJsonDocument.fromJson(json.encode())
    elements = document.array().toVariantList() if document.isArray() else []
    return elements[0] if elements else None


def encode(value: Any) -> str:
    array = QJsonArray()
    array.append(QJsonValue.fromVariant(value))
    return bytes(QJsonDocument(array).toJson(QJsonDocument.JsonFormat.Compact).data()).decode()


def bytes_used_by_other_keys(extension_id: str, key: str) -> int:
    query = sql.run(USED_BYTES, [extension_id, key])
    return int(query.value(0)) if query is not None and query.next() else 0


def exceeds_quota(extension_id: str, key: str, json: str) -> bool:
    total = bytes_used_by_other_keys(extension_id, key) + len(key.encode()) + len(json.encode())
    return total > STORAGE_QUOTA


def insert_value(extension_id: str, key: str, json: str) -> StorageWrite:
    if sql.run(INSERT_VALUE, [extension_id, key, json]) is not None:
        return StorageWrite(True)
    return StorageWrite(False, translated(NOT_AVAILABLE))


def value(extension_id: str, key: str) -> Any:
    query = sql.run(
        "SELECT value FROM extension_storage WHERE extension_id = ? AND key = ?",
        [extension_id, key],
    )
    if query is None or not query.next():
        return None
    return first_element(str(query.value(0)))


def set_value(extension_id: str, key: str, new_value: Any) -> StorageWrite:
    if not database.Database.instance().is_valid():
        return StorageWrite(False, translated(NOT_AVAILABLE))
    json = encode(new_value)
    if exceeds_quota(extension_id, key, json):
        return StorageWrite(False, translated(STORAGE_FULL))
    return insert_value(extension_id, key, json)


def remove_value(extension_id: str, key: str) -> None:
    sql.run("DELETE FROM extension_storage WHERE extension_id = ? AND key = ?", [extension_id, key])


def keys(extension_id: str) -> list[str]:
    query = sql.run(
        "SELECT key FROM extension_storage WHERE extension_id = ? ORDER BY key", [extension_id]
    )
    result: list[str] = []
    while query is not None and query.next():
        result.append(str(query.value(0)))
    return result


def remove_extension(extension_id: str) -> None:
    sql.run("DELETE FROM extension_storage WHERE extension_id = ?", [extension_id])
