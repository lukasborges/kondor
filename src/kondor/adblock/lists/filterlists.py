from pathlib import Path
from typing import NamedTuple

from PySide6.QtCore import QDateTime, QFileInfo, QStandardPaths

from kondor.adblock.filters.filterengine import FilterEngine

MAX_CACHE_AGE_DAYS = 4
CACHE_FOLDER = "/adblock"


class FilterListSource(NamedTuple):
    url: str
    file_name: str


FILTER_LIST_SOURCES = (
    FilterListSource("https://easylist.to/easylist/easylist.txt", "easylist.txt"),
    FilterListSource("https://easylist.to/easylist/easyprivacy.txt", "easyprivacy.txt"),
)


def filter_list_sources() -> tuple[FilterListSource, ...]:
    return FILTER_LIST_SOURCES


def filter_cache_directory() -> str:
    location = QStandardPaths.StandardLocation.AppDataLocation
    return str(QStandardPaths.writableLocation(location)) + CACHE_FOLDER


def filter_cache_path(source: FilterListSource) -> str:
    return f"{filter_cache_directory()}/{source.file_name}"


def cached_filter_list_files() -> list[str]:
    return [filter_cache_path(source) for source in filter_list_sources()]


def is_missing_from_cache(source: FilterListSource) -> bool:
    return not bool(QFileInfo.exists(filter_cache_path(source)))


def is_too_old(last_update: QDateTime) -> bool:
    return int(last_update.daysTo(QDateTime.currentDateTime())) >= MAX_CACHE_AGE_DAYS


def is_cache_stale(last_update: QDateTime) -> bool:
    if not last_update.isValid() or is_too_old(last_update):
        return True
    return any(is_missing_from_cache(source) for source in filter_list_sources())


def read_list(path: str) -> bytes:
    try:
        return Path(path).read_bytes()
    except OSError:
        return b""


def parse_filter_lists(files: list[str]) -> FilterEngine:
    engine = FilterEngine()
    for path in files:
        engine.add_list(read_list(path))
    return engine
