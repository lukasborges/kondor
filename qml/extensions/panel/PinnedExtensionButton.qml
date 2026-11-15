import QtQuick
import QtQuick.Controls
import Kondor

ToolButton {
    id: root

    required property var modelData
    required property bool isPrivate
    required property Item focusTarget
    readonly property bool hasIconFile: modelData.iconSource.includes("/")

    function isContextMenuKey(event) {
        return event.key === Qt.Key_F10 && (event.modifiers & Qt.ShiftModifier)
    }

    function openMenuUnderButton() {
        if (!isPrivate)
            unpinMenu.popup(root, 0, root.height)
    }

    function unpinAndRestoreFocus() {
        focusTarget.forceActiveFocus(Qt.PopupFocusReason)
        ExtensionManager.setPinned(modelData.id, false)
    }

    display: AbstractButton.IconOnly
    icon.name: hasIconFile ? "" : modelData.iconSource
    icon.source: hasIconFile ? modelData.iconSource : ""
    icon.color: "transparent"
    ToolTip.visible: hovered
    ToolTip.text: modelData.name
    ToolTip.delay: 600
    Accessible.name: modelData.name
    Keys.onMenuPressed: openMenuUnderButton()
    Keys.onPressed: function(event) {
        if (root.isContextMenuKey(event))
            root.openMenuUnderButton()
        event.accepted = root.isContextMenuKey(event)
    }

    TapHandler {
        acceptedButtons: Qt.RightButton
        enabled: !root.isPrivate
        onTapped: function(eventPoint) { unpinMenu.popup(eventPoint.position.x, eventPoint.position.y) }
    }

    Menu {
        id: unpinMenu
        objectName: "unpinMenu"

        MenuItem {
            objectName: "unpinMenuItem"
            text: qsTr("Unpin from Toolbar")
            icon.name: "window-unpin"
            onTriggered: root.unpinAndRestoreFocus()
        }
    }
}
