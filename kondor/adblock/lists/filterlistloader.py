import threading

from PySide6.QtCore import QObject, Signal, Slot

from kondor.adblock.filters.filterengine import FilterEngine
from kondor.adblock.lists.filterlists import parse_filter_lists


class FilterListLoader(QObject):
    loaded = Signal(object)
    _parsed = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._is_running = False
        self._parsed.connect(self._hand_over)

    def load(self, files: list[str]) -> None:
        self._is_running = True
        worker = threading.Thread(target=self._parse, args=(list(files),), daemon=True)
        worker.start()

    def is_running(self) -> bool:
        return self._is_running

    def _parse(self, files: list[str]) -> None:
        self._parsed.emit(parse_filter_lists(files))

    @Slot(object)
    def _hand_over(self, engine: FilterEngine) -> None:
        self._is_running = False
        self.loaded.emit(engine)
