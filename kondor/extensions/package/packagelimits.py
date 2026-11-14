from dataclasses import dataclass

from PySide6.QtCore import QCoreApplication, QDir, QDirIterator

MAX_PACKAGE_BYTES = 5 * 1024 * 1024
MAX_PACKAGE_FILES = 200
BYTES_PER_MIB = 1024 * 1024


@dataclass
class PackageSize:
    bytes: int = 0
    files: int = 0


def measure_directory(directory: str) -> PackageSize:
    size = PackageSize()
    flags = QDir.Filter.Files | QDir.Filter.NoSymLinks
    iterator = QDirIterator(directory, flags, QDirIterator.IteratorFlag.Subdirectories)
    while iterator.hasNext():
        iterator.next()
        size.bytes += iterator.fileInfo().size()
        size.files += 1
    return size


def translated(text: str) -> str:
    return str(QCoreApplication.translate("ExtensionPackage", text))


def package_limit_error(size: PackageSize) -> str:
    if size.files > MAX_PACKAGE_FILES:
        text = translated("The package has more than %1 files")
        return text.replace("%1", str(MAX_PACKAGE_FILES))
    if size.bytes > MAX_PACKAGE_BYTES:
        text = translated("The package is larger than %1 MiB")
        return text.replace("%1", str(MAX_PACKAGE_BYTES // BYTES_PER_MIB))
    return ""
