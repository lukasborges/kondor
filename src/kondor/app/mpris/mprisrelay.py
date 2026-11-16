from PySide6.QtCore import QObject, Signal

from kondor.app.mpris.mprissnapshot import tab_of
from kondor.browser.tabs.features.tabmedia import TabMedia


class MediaRelay(QObject):
    changed = Signal()
    seeked = Signal()
    titleChanged = Signal()

    def __init__(self, media: TabMedia) -> None:
        super().__init__()
        media.changed.connect(self.changed)
        media.playingChanged.connect(self.changed)
        media.seeked.connect(self.seeked)
        tab = tab_of(media)
        if tab is not None:
            tab.titleChanged.connect(self.titleChanged)
