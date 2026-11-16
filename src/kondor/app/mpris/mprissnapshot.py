from PySide6.QtGui import QGuiApplication

from kondor.app.mpris.mprisproperties import PlayerSnapshot
from kondor.browser.media.mediastate import MediaState
from kondor.browser.tabs.features.tabmedia import TabMedia
from kondor.browser.tabs.tab import Tab


def tab_of(media: TabMedia | None) -> Tab | None:
    tab = media.parent() if media is not None else None
    return tab if isinstance(tab, Tab) else None


def snapshot_of(media: TabMedia | None, track_number: int) -> PlayerSnapshot:
    tab = tab_of(media)
    return PlayerSnapshot(
        state=media.state if media is not None else MediaState(),
        position=media.current_position() if media is not None else 0.0,
        track_number=track_number,
        url=tab.url.toString() if tab is not None else "",
        is_private=tab.isPrivate if tab is not None else False,
        identity=QGuiApplication.applicationDisplayName(),
    )
