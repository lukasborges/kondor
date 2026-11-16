import time
from collections.abc import Callable
from dataclasses import replace

from PySide6.QtCore import Property, QObject, Signal, Slot

from kondor.browser.media.mediastate import MediaState
from kondor.browser.media.mediatabs import MediaTabs


def without_live_values(state: MediaState) -> MediaState:
    return replace(state, position=0.0, was_seeked=False)


class TabMedia(QObject):
    changed = Signal()
    playingChanged = Signal()
    seeked = Signal()
    actionRequested = Signal(str, float)

    def __init__(
        self, parent: QObject | None = None, clock: Callable[[], float] = time.monotonic
    ) -> None:
        super().__init__(parent)
        self._clock = clock
        self._state = MediaState()
        self._reported_at = clock()
        MediaTabs.instance().watch(self)

    @property
    def state(self) -> MediaState:
        return self._state

    hasMedia = Property(bool, lambda self: self._state.has_media, notify=changed)
    isPlaying = Property(bool, lambda self: self._state.is_playing, notify=playingChanged)

    def apply(self, state: MediaState) -> None:
        previous = self._state
        self._state = state
        self._reported_at = self._clock()
        if without_live_values(previous) != without_live_values(state):
            self.changed.emit()
        if previous.is_playing != state.is_playing:
            self.playingChanged.emit()
        if state.was_seeked:
            self.seeked.emit()

    def clear(self) -> None:
        self.apply(MediaState())

    def current_position(self) -> float:
        state = self._state
        if not state.is_playing:
            return state.position
        position = state.position + state.rate * (self._clock() - self._reported_at)
        return min(position, state.duration) if state.duration > 0 else position

    @Slot()
    def play(self) -> None:
        self.actionRequested.emit("play", 0.0)

    @Slot()
    def pause(self) -> None:
        self.actionRequested.emit("pause", 0.0)

    @Slot()
    def togglePlayback(self) -> None:
        self.pause() if self._state.is_playing else self.play()

    @Slot()
    def stop(self) -> None:
        self.actionRequested.emit("stop", 0.0)

    @Slot()
    def next(self) -> None:
        self.actionRequested.emit("nexttrack", 0.0)

    @Slot()
    def previous(self) -> None:
        self.actionRequested.emit("previoustrack", 0.0)

    @Slot(float)
    def seekTo(self, seconds: float) -> None:
        self.actionRequested.emit("seekto", seconds)
