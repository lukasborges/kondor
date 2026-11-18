import QtQuick
import QtQuick.Layouts
import Kondor

ColumnLayout {
    id: root

    required property TabModel tabs
    required property var browserWindow

    readonly property alias findBar: findBar

    spacing: 0

    ResponsiveToolBar {
        tab: root.tabs.currentTab
        visible: root.tabs.currentTab !== null && root.tabs.currentTab.responsive.isActive
        Layout.fillWidth: true
    }

    CrashReportBar {
        isEligible: !root.browserWindow.privateWindow
        onReportRequested: function(address) { root.browserWindow.openUrlInNewTab(address) }
    }

    PermissionBar {
        tab: root.tabs.currentTab
        Layout.fillWidth: true
    }

    PasswordBar {
        tab: root.tabs.currentTab
        Layout.fillWidth: true
    }

    SiteReloadBar {
        tab: root.tabs.currentTab
        Layout.fillWidth: true
    }

    IdentityBar {
        tab: root.tabs.currentTab
        Layout.fillWidth: true
    }

    UserScriptBar {
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
                browserActions: root.browserWindow.actions
                anchors.fill: parent
                visible: root.tabs.currentTab === tab
            }
        }
    }
}
