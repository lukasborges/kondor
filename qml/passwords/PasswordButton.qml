import QtQuick
import QtQuick.Controls
import Kondor

ToolButton {
    id: root

    required property TabModel tabs

    visible: tabs.currentTab ? tabs.currentTab.passwordUsernames.length > 0 : false
    display: AbstractButton.IconOnly
    icon.name: "dialog-password"
    icon.width: 16
    icon.height: 16
    flat: true
    implicitWidth: 28
    implicitHeight: 28
    ToolTip.visible: hovered
    ToolTip.text: qsTr("Fill Saved Password")
    ToolTip.delay: 600
    onClicked: passwordMenu.popup(root, 0, root.height)

    Menu {
        id: passwordMenu

        Instantiator {
            model: root.tabs.currentTab ? root.tabs.currentTab.passwordUsernames : []
            delegate: MenuItem {
                required property string modelData
                text: modelData
                icon.name: "user-identity"
                onTriggered: root.tabs.currentTab.fillPassword(modelData)
            }
            onObjectAdded: function(index, object) { passwordMenu.insertItem(index, object) }
            onObjectRemoved: function(index, object) { passwordMenu.removeItem(object) }
        }
    }
}
