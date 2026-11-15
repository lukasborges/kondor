from dataclasses import dataclass

from kondor.extensions.package.extensionpackage import ExtensionPackage


@dataclass
class PackageFile:
    zip_path: str
    source: str
    label: str = ""
    is_temporary: bool = False


@dataclass
class StagedPackage:
    directory: str
    package: ExtensionPackage
    file: PackageFile
