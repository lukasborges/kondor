import weakref
from typing import TYPE_CHECKING, ClassVar

from PySide6.QtCore import QObject, Signal
from shiboken6 import isValid

if TYPE_CHECKING:
    from kondor.browser.tabs.features.tabmedia import TabMedia

WatchedMedia = tuple[int, "weakref.ref[TabMedia]"]


def live_media(entry: WatchedMedia) -> "TabMedia | None":
    media = entry[1]()
    return media if media is not None and isValid(media) else None


class MediaTabs(QObject):
    currentChanged = Signal()
    _instance: ClassVar["MediaTabs | None"] = None

    def __init__(self) -> None:
        super().__init__()
        self._started: list[WatchedMedia] = []
        self._announced_key: int | None = None

    @classmethod
    def instance(cls) -> "MediaTabs":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def current(self) -> "TabMedia | None":
        return next(filter(None, map(live_media, self._started)), None)

    def watch(self, media: "TabMedia") -> None:
        entry = (id(media), weakref.ref(media))
        media.playingChanged.connect(lambda: self._follow_playback(entry))
        media.changed.connect(lambda: self._drop_if_without_media(entry))
        media.destroyed.connect(lambda: self._remove(entry[0]))

    def _follow_playback(self, entry: WatchedMedia) -> None:
        media = live_media(entry)
        if media is None or not media.state.is_playing:
            return
        self._started = [other for other in self._started if other[0] != entry[0]]
        self._started.insert(0, entry)
        self._announce_if_changed()

    def _drop_if_without_media(self, entry: WatchedMedia) -> None:
        media = live_media(entry)
        if media is not None and not media.state.has_media:
            self._remove(entry[0])

    def _remove(self, key: int) -> None:
        self._started = [other for other in self._started if other[0] != key]
        self._announce_if_changed()

    def _announce_if_changed(self) -> None:
        current = self.current
        key = None if current is None else id(current)
        if key != self._announced_key:
            self._announced_key = key
            self.currentChanged.emit()
