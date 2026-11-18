from kondor.browser.tabs.strip.tabstripmodel import TabStripModel


class Signals:
    def __init__(self, strip: TabStripModel) -> None:
        self.inserted: list[tuple[int, int]] = []
        self.removed: list[tuple[int, int]] = []
        self.moved: list[tuple[int, int, int]] = []
        self.changed: list[tuple[int, int]] = []
        self.resets = 0
        strip.rowsInserted.connect(lambda _p, first, last: self.inserted.append((first, last)))
        strip.rowsRemoved.connect(lambda _p, first, last: self.removed.append((first, last)))
        strip.rowsMoved.connect(
            lambda _p, first, last, _d, target: self.moved.append((first, last, target))
        )
        strip.dataChanged.connect(
            lambda top, bottom: self.changed.append((top.row(), bottom.row()))
        )
        strip.modelReset.connect(self.count_reset)

    def count_reset(self) -> None:
        self.resets += 1

    def structure_is_untouched(self) -> bool:
        return not (self.inserted or self.removed or self.moved or self.resets)
