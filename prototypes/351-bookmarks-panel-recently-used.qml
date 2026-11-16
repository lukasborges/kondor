// #351 Bookmarks panel: Recently Used, then the Bookmarks Toolbar contents (the only root folder).
import QtQuick
import QtQuick.Controls
import "common"

BrowserFrame {
    id: frame
    height: 560
    addressRight: [ ToolButton { icon.name: "non-starred-symbolic"; icon.width: 16; icon.height: 16; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 } ]
    toolbarExtras: [ ToolButton { icon.name: "bookmarks"; display: AbstractButton.IconOnly; checked: true } ]
    FakePage {}
    BookmarksPanelMock {
        x: frame.width - width - 40
        y: -6
        level: "list"
        oneRoot: true
    }
}
