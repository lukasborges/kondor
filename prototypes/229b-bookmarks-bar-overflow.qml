// #229 Bookmarks bar: the window is narrow; the items that do not fit are in the » menu, and a
// link dragged from the page shows where it will land (blue line before "Qt Docs").
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "common"

BrowserFrame {
    id: frame
    width: 760
    height: 330
    belowHeader: [ BookmarksBarMock { pressedIndex: 99; dropAt: 2; visibleCount: 5 } ]
    FakePage {}
    Menu {
        popupType: Popup.Item
        x: frame.width - width - 4; y: 0
        Component.onCompleted: open()
        MenuItem { text: "Linux Weekly News"; icon.name: "globe" }
        MenuItem { text: "Wikipedia"; icon.name: "internet-web-browser" }
        MenuItem { text: "Kirigami Gallery"; icon.name: "kde" }
    }
}
