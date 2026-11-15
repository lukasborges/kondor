from dataclasses import dataclass, field
from io import BufferedReader
from pathlib import Path

from PySide6.QtCore import QUrl

MAX_IMPORT_BYTES = 20 * 1024 * 1024
UNREADABLE = "unreadable"
TOO_LARGE = "tooLarge"


@dataclass
class ImportFile:
    data: bytearray = field(default_factory=bytearray)
    error: str = ""


def zero(data: bytearray) -> None:
    data[:] = bytes(len(data))


def read_within_limit(source: BufferedReader) -> ImportFile:
    data = bytearray(MAX_IMPORT_BYTES + 1)
    count = source.readinto(data)
    if count > MAX_IMPORT_BYTES:
        zero(data)
        return ImportFile(error=TOO_LARGE)
    del data[count:]
    return ImportFile(data)


def read_local_file(path: Path) -> ImportFile:
    if path.stat().st_size > MAX_IMPORT_BYTES:
        return ImportFile(error=TOO_LARGE)
    with path.open("rb") as source:
        return read_within_limit(source)


def read_import_file(file: QUrl) -> ImportFile:
    path = Path(file.toLocalFile())
    if not file.isLocalFile() or not path.is_file():
        return ImportFile(error=UNREADABLE)
    try:
        return read_local_file(path)
    except OSError:
        return ImportFile(error=UNREADABLE)
