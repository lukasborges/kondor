from dataclasses import dataclass, field
from typing import Any

from kondor.extensions.package.extensionpackage import ExtensionPackage
from kondor.extensions.state.extensionstate import ExtensionState

NOT_FOUND = -1
JsonMap = dict[str, Any]


@dataclass
class InstalledExtension:
    package: ExtensionPackage
    enabled: bool = True
    private_allowed: bool = False
    source: str = ""
    token: str = ""
    update_available: bool = False
    update_needs_review: bool = False


@dataclass
class ExtensionContext:
    state: ExtensionState
    entries: list[InstalledExtension] = field(default_factory=list)
    locale: str = ""


def index_of(entries: list[InstalledExtension], extension_id: str) -> int:
    for row, entry in enumerate(entries):
        if entry.package.id() == extension_id:
            return row
    return NOT_FOUND


def find(entries: list[InstalledExtension], extension_id: str) -> InstalledExtension | None:
    row = index_of(entries, extension_id)
    return None if row < 0 else entries[row]
