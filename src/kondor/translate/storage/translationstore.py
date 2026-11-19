import json
import shutil
from pathlib import Path
from typing import NamedTuple

from PySide6.QtCore import QStandardPaths

Pair = tuple[str, str]
READY_MARKER = "ready.json"
ENGINE_FILE = "bergamot-translator.wasm"
PARTIAL_SUFFIX = ".partial"
BYTES_PER_MB = 1_000_000


class InstalledPair(NamedTuple):
    source: str
    target: str
    size_bytes: int


def default_root() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    return Path(base) / "translations"


def directory_size(directory: Path) -> int:
    return sum(path.stat().st_size for path in directory.iterdir() if path.is_file())


class TranslationStore:
    def __init__(self, root: Path | None = None) -> None:
        self._root = root if root is not None else default_root()

    @property
    def engine_directory(self) -> Path:
        return self._root / "engine"

    @property
    def page_directory(self) -> Path:
        return self._root / "page"

    @property
    def catalog_path(self) -> Path:
        return self._root / "catalog.json"

    @property
    def engine_path(self) -> Path:
        return self.engine_directory / ENGINE_FILE

    def pair_directory(self, pair: Pair) -> Path:
        return self._root / "models" / f"{pair[0]}-{pair[1]}"

    def partial_directory(self, directory: Path) -> Path:
        return directory.with_name(directory.name + PARTIAL_SUFFIX)

    def is_pair_installed(self, pair: Pair) -> bool:
        return (self.pair_directory(pair) / READY_MARKER).is_file()

    def is_engine_installed(self) -> bool:
        return self.engine_path.is_file() and (self.engine_directory / READY_MARKER).is_file()

    def pair_files(self, pair: Pair) -> dict[str, Path]:
        marker = self.pair_directory(pair) / READY_MARKER
        names: dict[str, str] = json.loads(marker.read_text(encoding="utf-8"))
        return {kind: marker.parent / name for kind, name in names.items()}

    def installed_pairs(self) -> list[InstalledPair]:
        models = self._root / "models"
        directories = sorted(models.iterdir()) if models.is_dir() else []
        return [self._installed(path) for path in directories if self._is_ready(path)]

    def remove_pair(self, pair: Pair) -> None:
        shutil.rmtree(self.pair_directory(pair), ignore_errors=True)

    def discard_partial(self, directory: Path) -> None:
        shutil.rmtree(self.partial_directory(directory), ignore_errors=True)

    def publish(self, directory: Path, names: dict[str, str]) -> None:
        partial = self.partial_directory(directory)
        (partial / READY_MARKER).write_text(json.dumps(names), encoding="utf-8")
        shutil.rmtree(directory, ignore_errors=True)
        partial.rename(directory)

    def _is_ready(self, path: Path) -> bool:
        return path.is_dir() and (path / READY_MARKER).is_file() and "-" in path.name

    def _installed(self, path: Path) -> InstalledPair:
        source, target = path.name.split("-", 1)
        return InstalledPair(source, target, directory_size(path))
