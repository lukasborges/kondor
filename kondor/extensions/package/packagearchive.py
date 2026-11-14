import stat
import zipfile
from dataclasses import dataclass, field

from PySide6.QtCore import QCoreApplication, QDir, QFileInfo

from kondor.extensions.package.packagelimits import PackageSize, package_limit_error
from kondor.extensions.package.packagepath import is_safe_relative_path


@dataclass
class ArchiveListing:
    entries: list[zipfile.ZipInfo] = field(default_factory=list)
    size: PackageSize = field(default_factory=PackageSize)
    error: str = ""


def translated(text: str) -> str:
    return str(QCoreApplication.translate("ExtensionPackage", text))


def add_entry(info: zipfile.ZipInfo, listing: ArchiveListing) -> None:
    if not is_safe_relative_path(info.filename):
        listing.error = translated("Unsafe file name in the package: %1").replace(
            "%1", info.filename
        )
        return
    listing.size.bytes += info.file_size
    listing.size.files += 1
    listing.entries.append(info)
    listing.error = package_limit_error(listing.size)


def list_entries(archive: zipfile.ZipFile) -> ArchiveListing:
    listing = ArchiveListing()
    for info in archive.infolist():
        if listing.error:
            break
        if not info.is_dir():
            add_entry(info, listing)
    return listing


def is_symbolic_link(info: zipfile.ZipInfo) -> bool:
    return stat.S_ISLNK(info.external_attr >> 16)


def write_entry(archive: zipfile.ZipFile, info: zipfile.ZipInfo, target: QDir) -> bool:
    destination = target.filePath(info.filename)
    QDir().mkpath(QFileInfo(destination).absolutePath())
    try:
        data = archive.read(info)
        with open(destination, "wb") as out:
            return out.write(data) == len(data)
    except (zipfile.BadZipFile, OSError):
        return False


def write_entries(archive: zipfile.ZipFile, listing: ArchiveListing, directory: str) -> str:
    target = QDir(directory)
    for info in listing.entries:
        if not is_symbolic_link(info) and not write_entry(archive, info, target):
            return translated("Cannot write %1").replace("%1", info.filename)
    return ""


def unpack_archive(archive: zipfile.ZipFile, directory: str) -> str:
    listing = list_entries(archive)
    if listing.error:
        return listing.error
    if not QDir().mkpath(directory):
        return translated("Cannot create %1").replace("%1", directory)
    return write_entries(archive, listing, directory)


def unpack(zip_path: str, directory: str) -> str:
    try:
        with zipfile.ZipFile(zip_path) as archive:
            return unpack_archive(archive, directory)
    except (zipfile.BadZipFile, OSError):
        return translated("The file is not a valid ZIP archive")
