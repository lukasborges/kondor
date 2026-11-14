// #229 Bookmarks bar: a folder menu with "Open All in Tabs" and "Add This Page Here".
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "common"

BrowserFrame {
    id: frame
    height: 360
    belowHeader: [ BookmarksBarMock { pressedIndex: 3 } ]
    FakePage {}
    Menu {
        popupType: Popup.Item
        x: 300; y: 0
        Component.onCompleted: open()
        MenuItem { text: "OMG! Ubuntu"; icon.name: "globe" }
        MenuItem { text: "Phoronix"; icon.name: "globe" }
        MenuItem { text: "LWN.net"; icon.name: "globe" }
        MenuItem { text: "This Week in KDE"; icon.name: "kde" }
        MenuSeparator {}
        MenuItem { text: "Open All in Tabs (4)"; icon.name: "tab-new" }
        MenuItem { text: "Add This Page Here"; icon.name: "bookmark-new" }
    }
}
