import QtQuick
import QtQuick.Controls
import Kondor

ToolButton {
    id: root

    required property TabModel tabs
    required property var browserWindow

    function togglePanel() {
        panel.opened ? panel.close() : panel.open()
    }

    display: AbstractButton.IconOnly
    icon.name: "bookmarks"
    checked: panel.opened
    ToolTip.visible: hovered
    Accessible.name: ToolTip.text
    ToolTip.text: qsTr("Bookmarks")
    ToolTip.delay: 600
    onClicked: togglePanel()

    BookmarksPanel {
        id: panel
        objectName: "bookmarksPanel"
        tab: root.tabs.currentTab
        browserWindow: root.browserWindow
    }
}
