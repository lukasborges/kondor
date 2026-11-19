from typing import NamedTuple

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QNetworkAccessManager

from kondor.translate.catalog.records import FileRecord
from kondor.translate.catalog.selection import PairFiles, select_engine, select_models
from kondor.translate.download.jsonfetch import fetch_json

SERVER = "https://firefox.settings.services.mozilla.com/v1/"
RECORDS = SERVER + "buckets/main/collections/{}/records"
WASM_COLLECTION = "translations-wasm"
MODELS_COLLECTION = "translations-models"


class Catalog(NamedTuple):
    engine: FileRecord | None
    models: dict[tuple[str, str], PairFiles]
    base_url: str


class RawCatalog(NamedTuple):
    engine: list[dict[str, object]]
    models: list[dict[str, object]]
    base_url: str


def build_catalog(raw: RawCatalog) -> Catalog:
    return Catalog(select_engine(raw.engine), select_models(raw.models), raw.base_url)


def record_list(response: object | None) -> list[dict[str, object]] | None:
    data = response.get("data") if isinstance(response, dict) else None
    return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else None


def attachments_base_url(response: object | None) -> str | None:
    capabilities = response.get("capabilities") if isinstance(response, dict) else None
    attachments = capabilities.get("attachments") if isinstance(capabilities, dict) else None
    url = attachments.get("base_url") if isinstance(attachments, dict) else None
    return url if isinstance(url, str) and url.startswith("https://") else None


class CatalogLoader(QObject):
    loaded = Signal(object)
    failed = Signal()

    def __init__(self, manager: QNetworkAccessManager, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._base_url = ""
        self._engine: list[dict[str, object]] = []

    def start(self) -> None:
        fetch_json(self._manager, SERVER, self._on_server)

    def _on_server(self, response: object | None) -> None:
        base_url = attachments_base_url(response)
        if base_url is None:
            self.failed.emit()
            return
        self._base_url = base_url
        fetch_json(self._manager, RECORDS.format(WASM_COLLECTION), self._on_engine)

    def _on_engine(self, response: object | None) -> None:
        records = record_list(response)
        if records is None:
            self.failed.emit()
            return
        self._engine = records
        fetch_json(self._manager, RECORDS.format(MODELS_COLLECTION), self._on_models)

    def _on_models(self, response: object | None) -> None:
        records = record_list(response)
        if records is None:
            self.failed.emit()
            return
        self.loaded.emit(RawCatalog(self._engine, records, self._base_url))
