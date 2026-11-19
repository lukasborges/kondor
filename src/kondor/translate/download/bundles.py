from pathlib import Path
from typing import NamedTuple

from kondor.translate.catalog.records import FileRecord
from kondor.translate.download.catalogloader import Catalog
from kondor.translate.download.filedownloader import FileTask
from kondor.translate.storage.translationstore import ENGINE_FILE, Pair, TranslationStore

ENGINE_KIND = "engine"


class Bundle(NamedTuple):
    directory: Path
    files: dict[str, FileRecord]


def attachment_url(base_url: str, record: FileRecord) -> str:
    return base_url.rstrip("/") + "/" + record.location


def file_name(kind: str, record: FileRecord) -> str:
    return ENGINE_FILE if kind == ENGINE_KIND else record.name


def file_names(bundle: Bundle) -> dict[str, str]:
    return {kind: file_name(kind, record) for kind, record in bundle.files.items()}


def engine_bundles(store: TranslationStore, catalog: Catalog) -> list[Bundle]:
    if store.is_engine_installed() or catalog.engine is None:
        return []
    return [Bundle(store.engine_directory, {ENGINE_KIND: catalog.engine})]


def pair_bundles(store: TranslationStore, catalog: Catalog, route: list[Pair]) -> list[Bundle]:
    missing = [pair for pair in route if not store.is_pair_installed(pair)]
    return [Bundle(store.pair_directory(pair), catalog.models[pair]) for pair in missing]


def missing_bundles(store: TranslationStore, catalog: Catalog, route: list[Pair]) -> list[Bundle]:
    return engine_bundles(store, catalog) + pair_bundles(store, catalog, route)


def bundle_tasks(store: TranslationStore, base_url: str, bundle: Bundle) -> list[FileTask]:
    partial = store.partial_directory(bundle.directory)
    return [
        FileTask(
            attachment_url(base_url, record),
            partial / file_name(kind, record),
            record.hash,
            record.size,
        )
        for kind, record in bundle.files.items()
    ]


def total_bytes(bundles: list[Bundle]) -> int:
    return sum(record.size for bundle in bundles for record in bundle.files.values())
