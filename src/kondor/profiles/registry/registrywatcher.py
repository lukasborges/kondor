from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, Signal, Slot

from kondor.profiles.registry.registrystore import open_registry


class RegistryWatcher(QObject):
    changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._watcher = QFileSystemWatcher(self)
        self._path = Path(open_registry().fileName())
        self._watcher.fileChanged.connect(self._on_changed)
        self._watcher.directoryChanged.connect(self._on_changed)
        self._watch()

    def _watch(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        watched = self._watcher.files() + self._watcher.directories()
        wanted = [str(self._path), str(self._path.parent)]
        missing = [path for path in wanted if path not in watched and Path(path).exists()]
        if missing:
            self._watcher.addPaths(missing)

    @Slot()
    def _on_changed(self) -> None:
        self._watch()
        self.changed.emit()
