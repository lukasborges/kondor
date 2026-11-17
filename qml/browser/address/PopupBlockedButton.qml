import QtQuick
import QtQuick.Controls
import Kondor

ToolButton {
    id: root

    required property TabModel tabs
    required property Item addressField

    readonly property var blockedUrls: tabs.currentTab ? tabs.currentTab.popups.blockedUrls : []

    signal openRequested(string url)

    visible: blockedUrls.length > 0
    display: AbstractButton.IconOnly
    focusPolicy: Qt.TabFocus
    icon.name: "window-duplicate-symbolic"
    icon.width: 16
    icon.height: 16
    flat: true
    checked: panel.opened
    implicitWidth: 28
    implicitHeight: 28
    ToolTip.visible: hovered
    Accessible.name: ToolTip.text
    ToolTip.text: qsTr("Pop-ups blocked")
    ToolTip.delay: 600
    onClicked: panel.opened ? panel.close() : panel.open()
    onVisibleChanged: {
        if (visible)
            Accessible.announce(qsTr("Pop-up blocked"))
        else
            panel.close()
    }

    BlockedPopupsPanel {
        id: panel
        parent: root.addressField
        popups: root.tabs.currentTab ? root.tabs.currentTab.popups : null
        x: root.addressField.width - width - 96
        y: root.addressField.height
    }

    Connections {
        target: root.tabs.currentTab ? root.tabs.currentTab.popups : null
        function onOpenRequested(url) { root.openRequested(url) }
    }
}
