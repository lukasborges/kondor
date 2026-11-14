import os
import uuid

from PySide6.QtCore import QCoreApplication, QDir, QFile

from kondor.extensions.package.extensionpackage import ExtensionPackage
from kondor.extensions.package.packagearchive import unpack
from kondor.extensions.package.packagefile import PackageFile, StagedPackage

CONTEXT = "ExtensionManager"


def remove_directory(directory: str) -> None:
    QDir(directory).removeRecursively()


def new_directory_of(final_directory: str) -> str:
    return final_directory + ".new"


def old_directory_of(final_directory: str) -> str:
    return final_directory + ".old"


def failure(text: str, directory: str) -> str:
    return str(QCoreApplication.translate(CONTEXT, text)).replace("%1", directory)


def abandon_new(final_directory: str) -> bool:
    remove_directory(new_directory_of(final_directory))
    return False


def unpack_and_load(zip_path: str, directory: str) -> tuple[ExtensionPackage | None, str]:
    error = unpack(zip_path, directory)
    if not error:
        package, error = ExtensionPackage.load(directory)
        if not error:
            return package, ""
    remove_directory(directory)
    return None, error


def staging_directory_in(base: str) -> str:
    return f"{base}/.staging-{uuid.uuid4()}"


class ExtensionInstaller:
    def __init__(self, extensions_directory: str) -> None:
        self.extensions_directory = extensions_directory

    def final_directory_of(self, extension_id: str) -> str:
        return f"{self.extensions_directory}/{extension_id}"

    def stage(self, file: PackageFile) -> tuple[StagedPackage | None, str]:
        if not QDir().mkpath(self.extensions_directory):
            return None, failure("Cannot create %1", self.extensions_directory)
        directory = staging_directory_in(self.extensions_directory)
        package, error = unpack_and_load(file.zip_path, directory)
        if package is None:
            return None, error
        return StagedPackage(directory, package, file), ""

    def replace_existing(self, final_directory: str) -> str:
        if not os.path.lexists(final_directory):
            return ""
        if QDir().rename(final_directory, old_directory_of(final_directory)):
            return ""
        return failure("Cannot replace %1", final_directory)

    def move_to_new(self, staged: StagedPackage, final_directory: str) -> str:
        new_directory = new_directory_of(final_directory)
        if QDir().rename(staged.directory, new_directory):
            return ""
        return failure("Cannot install into %1", new_directory)

    def move_into_place(self, final_directory: str) -> str:
        error = self.replace_existing(final_directory)
        if not error and QDir().rename(new_directory_of(final_directory), final_directory):
            return ""
        old_directory = old_directory_of(final_directory)
        if not error and os.path.lexists(old_directory):
            QDir().rename(old_directory, final_directory)
        return error or failure("Cannot install into %1", final_directory)

    def commit(self, staged: StagedPackage) -> str:
        final_directory = self.final_directory_of(staged.package.id())
        remove_directory(new_directory_of(final_directory))
        remove_directory(old_directory_of(final_directory))
        error = self.move_to_new(staged, final_directory) or self.move_into_place(final_directory)
        if error:
            abandon_new(final_directory)
            return error
        remove_directory(old_directory_of(final_directory))
        return ""

    def discard(self, staged: StagedPackage) -> None:
        remove_directory(staged.directory)
        if staged.file.is_temporary:
            QFile.remove(staged.file.zip_path)
