import QtQuick
import QtQuick.Layouts
import Kondor

ColumnLayout {
    id: root

    required property TabModel tabs
    required property var browserWindow

    readonly property alias findBar: findBar

    spacing: 0

    PermissionBar {
        tab: root.tabs.currentTab
        Layout.fillWidth: true
    }

    PasswordBar {
        tab: root.tabs.currentTab
        Layout.fillWidth: true
    }

    FindBar {
        id: findBar
        tab: root.tabs.currentTab
        Layout.fillWidth: true
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.fillHeight: true
        color: root.browserWindow.palette.base

        Repeater {
            model: root.tabs

            delegate: WebViewTab {
                tabModel: root.tabs
                anchors.fill: parent
                visible: root.tabs.currentTab === tab
            }
        }
    }
}
