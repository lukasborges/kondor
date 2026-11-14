import json
import shutil
import zipfile
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import qWarning

from kondor.core.settings.settings import Settings
from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.package.packagefile import PackageFile

DATA_ROOT = Path(__file__).resolve().parent.parent / "data"
SAMPLE_FILES = ("content.js", "style.css", "icon.svg", "manifest.json")

ManifestEdit = Callable[[dict], None]


def data_dir(name: str) -> str:
    return str(DATA_ROOT / "extensions" / name)


def write_file(path: str, content: bytes) -> bool:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return Path(path).write_bytes(content) == len(content)


def zip_directory(directory: str, zip_path: str) -> bool:
    Path(zip_path).unlink(missing_ok=True)
    root = Path(directory)
    files = [file for file in sorted(root.rglob("*")) if file.is_file()]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            archive.write(file, file.relative_to(root).as_posix())
    return True


def copy_sample_files(directory: str) -> None:
    for name in SAMPLE_FILES:
        shutil.copy(Path(data_dir("sample")) / name, Path(directory) / name)


def make_variant(root: str, name: str, edit: ManifestEdit) -> str:
    directory = Path(root) / name
    shutil.rmtree(directory, ignore_errors=True)
    directory.mkdir(parents=True)
    copy_sample_files(str(directory))
    manifest = directory / "manifest.json"
    content = json.loads(manifest.read_text())
    edit(content)
    manifest.write_text(json.dumps(content, indent=4))
    return str(directory)


def pack_variant(root: str, name: str, edit: ManifestEdit) -> str:
    zip_path = f"{root}/{name}.kondorext"
    directory = make_variant(root, name, edit)
    return zip_path if zip_directory(directory, zip_path) else ""


def sample_package(work: str) -> str:
    path = f"{work}/sample.kondorext"
    if not Path(path).exists():
        zip_directory(data_dir("sample"), path)
    return path


def install_sample(work: str, source: str = "file") -> bool:
    result = ExtensionManager.instance().install_package(
        PackageFile(sample_package(work), source), "sample"
    )
    if not result.is_installed:
        qWarning(result.error)
    return result.is_installed


def rename_manifest(extension_id: str, name: str) -> ManifestEdit:
    def edit(manifest: dict) -> None:
        manifest["id"] = extension_id
        manifest["name"] = name

    return edit


def install_named(work: str, extension_id: str, name: str) -> bool:
    zip_path = pack_variant(work, extension_id, rename_manifest(extension_id, name))
    file = PackageFile(zip_path, "file")
    return ExtensionManager.instance().install_package(file, extension_id).is_installed


def plain_manifest(manifest: dict) -> None:
    manifest["id"] = "plain"
    manifest["name"] = "Plain"
    manifest["action"] = {"items": [{"id": "go", "title": "Go Now"}]}


def install_plain(work: str) -> bool:
    zip_path = pack_variant(work, "plain", plain_manifest)
    return (
        ExtensionManager.instance()
        .install_package(PackageFile(zip_path, "file"), "plain")
        .is_installed
    )


def apply_settings(extension_id: str, settings: dict) -> None:
    ExtensionManager.instance().applyConfiguration(extension_id, {"settings": settings})


def allow_in_private_windows(extension_id: str) -> None:
    ExtensionManager.instance().applyConfiguration(extension_id, {"privateAllowed": True})


def remove_every_extension() -> None:
    manager = ExtensionManager.instance()
    manager.cancelInstall()
    while manager.count > 0:
        manager.remove(manager.data(manager.index(0, 0), ExtensionManager.Role.IdRole))
    manager.set_locale("en")
    Settings.instance().setProperty("pinnedExtensions", [])
