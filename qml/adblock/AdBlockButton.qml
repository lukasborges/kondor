import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor

ToolButton {
    id: root

    required property TabModel tabs
    required property Item addressField

    readonly property string host: hostOf(tabs.currentTab ? tabs.currentTab.url.toString() : "")
    property int count: 0
    property bool allowed: false

    function hostOf(address) {
        const match = address.match(/^https?:\/\/([^\/?#:]+)/i)
        return match ? match[1].toLowerCase() : ""
    }

    function refresh() {
        count = AdBlockManager.blockedCount(host)
        allowed = AdBlockManager.isAllowed(host)
    }

    visible: host.length > 0 && tabs.currentTab && !tabs.currentTab.newTabPage
    display: AbstractButton.IconOnly
    icon.name: allowed || !AdBlockManager.enabled ? "security-low" : "security-high"
    icon.width: 16
    icon.height: 16
    flat: true
    checked: popup.opened
    implicitWidth: 28
    implicitHeight: 28
    ToolTip.visible: hovered
    Accessible.name: ToolTip.text
    ToolTip.text: qsTr("Ad and Tracker Blocking")
    ToolTip.delay: 600
    onHostChanged: refresh()
    Component.onCompleted: refresh()
    onClicked: popup.opened ? popup.close() : popup.open()

    Connections {
        target: AdBlockManager
        function onBlockedCountChanged(changedHost) {
            if (changedHost === root.host)
                root.refresh()
        }
        function onAllowListChanged() { root.refresh() }
    }

    Connections {
        target: Settings
        function onAdBlockAllowListChanged() { root.refresh() }
    }

    Rectangle {
        visible: root.count > 0
        anchors { right: parent.right; top: parent.top; rightMargin: 1; topMargin: 1 }
        width: Math.max(height, badge.implicitWidth + 6)
        height: 13
        radius: height / 2
        color: Kirigami.Theme.negativeBackgroundColor

        Label {
            id: badge
            anchors.centerIn: parent
            text: root.count > 99 ? "99+" : root.count
            color: Kirigami.Theme.negativeTextColor
            font.pixelSize: 9
            font.bold: true
        }
    }

    AdBlockPopup {
        id: popup
        parent: root.addressField
        tab: root.tabs.currentTab
        host: root.host
        x: root.addressField.width - width
        y: root.addressField.height
    }
}
