import sys
from pathlib import Path

from PySide6.QtCore import QResource

PROJECT_VERSION = "0.23.4"
MISSING_BUILD_MESSAGE = "Kondor: cannot find the staged build in {}; run python3 scripts/build.py"


def package_parent_directory() -> Path:
    return Path(__file__).resolve().parents[3]


def staged_build_directory() -> Path:
    parent = package_parent_directory()
    return parent if (parent / "kondor.rcc").exists() else parent.parent / "build" / "python"


def has_staged_files(directory: Path) -> bool:
    return (directory / "qml" / "Kondor" / "qmldir").exists() and (
        directory / "kondor.rcc"
    ).exists()


def load_staged_resources(directory: Path) -> bool:
    if not has_staged_files(directory):
        print(MISSING_BUILD_MESSAGE.format(directory), file=sys.stderr)
        return False
    return bool(QResource.registerResource(str(directory / "kondor.rcc")))
