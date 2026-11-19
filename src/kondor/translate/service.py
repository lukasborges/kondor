from collections.abc import Callable
from typing import ClassVar, NamedTuple, Self

from PySide6.QtCore import QObject
from PySide6.QtNetwork import QNetworkAccessManager

from kondor.translate.catalog.routes import (
    can_translate,
    plan_route,
    source_languages,
    target_languages,
)
from kondor.translate.download.bundles import Bundle, missing_bundles
from kondor.translate.download.catalogloader import (
    Catalog,
    CatalogLoader,
    RawCatalog,
    build_catalog,
)
from kondor.translate.download.filesjob import FilesJob
from kondor.translate.engine.translationengine import (
    DoneCallback,
    EngineJob,
    FailCallback,
    Step,
    TranslationEngine,
)
from kondor.translate.storage.catalogcache import load_cached, write_cache
from kondor.translate.storage.translationstore import InstalledPair, Pair, TranslationStore

ReadyCallback = Callable[[bool], None]


class BatchRequest(NamedTuple):
    route: list[Pair]
    texts: list[str]


class TranslationService(QObject):
    _instance: ClassVar["TranslationService | None"] = None

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, store: TranslationStore | None = None) -> None:
        super().__init__()
        self._store = store if store is not None else TranslationStore()
        self._manager = QNetworkAccessManager(self)
        self._engine = TranslationEngine(self._store, self)
        self._catalog: Catalog | None = None
        self._waiting: list[ReadyCallback] = []
        self._is_loading = False
        self._jobs: dict[tuple[Pair, ...], FilesJob] = {}

    @property
    def store(self) -> TranslationStore:
        return self._store

    def ensure_catalog(self, ready: ReadyCallback) -> None:
        if self._catalog is not None:
            ready(True)
            return
        self._waiting.append(ready)
        if not self._is_loading:
            self._load_catalog()

    def available_pairs(self) -> set[Pair]:
        return set(self._catalog.models) if self._catalog is not None else set()

    def is_offered(self, source: str, target: str) -> bool:
        return can_translate(self.available_pairs(), source, target)

    def route(self, source: str, target: str) -> list[Pair] | None:
        return plan_route(self.available_pairs(), source, target)

    def source_codes(self) -> list[str]:
        return source_languages(self.available_pairs())

    def target_codes(self) -> list[str]:
        return target_languages(self.available_pairs())

    def download(self, route: list[Pair]) -> FilesJob | None:
        key = tuple(route)
        if key in self._jobs:
            return self._jobs[key]
        if self._catalog is None:
            return None
        bundles = missing_bundles(self._store, self._catalog, route)
        if not bundles:
            return None
        return self._start_job(key, bundles)

    def translate(self, request: BatchRequest, done: DoneCallback, fail: FailCallback) -> None:
        steps = [Step(pair[0], pair[1], self._store.pair_files(pair)) for pair in request.route]
        self._engine.translate(EngineJob(steps, request.texts), done, fail)

    def active_jobs(self) -> list[FilesJob]:
        return list(self._jobs.values())

    def installed_pairs(self) -> list[InstalledPair]:
        return self._store.installed_pairs()

    def remove_pair(self, source: str, target: str) -> None:
        self._store.remove_pair((source, target))

    def _start_job(self, key: tuple[Pair, ...], bundles: list[Bundle]) -> FilesJob:
        assert self._catalog is not None
        job = FilesJob(self._manager, self._store, self)
        self._jobs[key] = job
        job.finished.connect(lambda _ok: self._forget_job(key, job))
        job.start(bundles, self._catalog.base_url)
        return job

    def _forget_job(self, key: tuple[Pair, ...], job: FilesJob) -> None:
        self._jobs.pop(key, None)
        job.deleteLater()

    def _load_catalog(self) -> None:
        cached = load_cached(self._store.catalog_path)
        if cached.is_fresh and cached.catalog is not None:
            self._finish_loading(cached.catalog)
        else:
            self._fetch_catalog(cached.catalog)

    def _fetch_catalog(self, fallback: Catalog | None) -> None:
        self._is_loading = True
        loader = CatalogLoader(self._manager, self)
        loader.loaded.connect(self._on_loaded)
        loader.failed.connect(lambda: self._finish_loading(fallback))
        loader.start()

    def _on_loaded(self, raw: RawCatalog) -> None:
        write_cache(self._store.catalog_path, raw)
        self._finish_loading(build_catalog(raw))

    def _finish_loading(self, catalog: Catalog | None) -> None:
        self._is_loading = False
        self._catalog = catalog
        waiting, self._waiting = self._waiting, []
        for ready in waiting:
            ready(catalog is not None)
