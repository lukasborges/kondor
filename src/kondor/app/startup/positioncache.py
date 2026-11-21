import os
from pathlib import Path

from PySide6.QtCore import QStandardPaths, qWarning

CACHE_FILE_NAME = "qtposition-geoclue2"
DISCARDING_TARGET = "/dev/null"


def position_cache_path() -> Path:
    data_directory = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.GenericDataLocation
    )
    return Path(data_directory) / CACHE_FILE_NAME


def is_discarding(cache: Path) -> bool:
    return cache.is_symlink() and os.readlink(cache) == DISCARDING_TARGET


def replace_with_discarding_link(cache: Path) -> None:
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.unlink(missing_ok=True)
    cache.symlink_to(DISCARDING_TARGET)


# Qt Positioning's GeoClue2 plugin has no switch to disable its last-position cache, and a
# private page must never leave a position on disk: https://github.com/lukasborges/kondor-browser/issues/271
def discard_position_cache() -> None:
    cache = position_cache_path()
    if is_discarding(cache):
        return
    try:
        replace_with_discarding_link(cache)
    except OSError as error:
        qWarning(f"Kondor: cannot turn off the position cache {cache}: {error}")
