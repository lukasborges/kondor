// #229 Bookmarks bar: right-click on a bookmark.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "common"

BrowserFrame {
    id: frame
    height: 330
    belowHeader: [ BookmarksBarMock { pressedIndex: 1 } ]
    FakePage {}
    Menu {
        popupType: Popup.Item
        x: 70; y: 0
        Component.onCompleted: open()
        MenuItem { text: "Open in New Tab"; icon.name: "tab-new" }
        MenuItem { text: "Open in New Window"; icon.name: "window-new" }
        MenuSeparator {}
        MenuItem { text: "Edit…"; icon.name: "document-edit" }
        MenuItem { text: "Delete"; icon.name: "edit-delete" }
    }
}
