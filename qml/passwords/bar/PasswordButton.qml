import QtQuick
import QtQuick.Controls
import Kondor

ToolButton {
    id: root

    required property TabModel tabs

    signal manageRequested()

    visible: tabs.currentTab ? tabs.currentTab.passwords.usernames.length > 0 : false
    display: AbstractButton.IconOnly
    icon.name: "dialog-password"
    icon.width: 16
    icon.height: 16
    flat: true
    checked: popup.opened
    implicitWidth: 28
    implicitHeight: 28
    ToolTip.visible: hovered && !popup.opened
    Accessible.name: ToolTip.text
    ToolTip.text: qsTr("Fill Saved Password")
    ToolTip.delay: 600
    onClicked: popup.opened ? popup.close() : popup.open()

    SavedPasswordsPopup {
        id: popup
        x: root.width - width
        y: root.height
        tab: root.tabs.currentTab
        onManageRequested: root.manageRequested()
    }
}
