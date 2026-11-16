import QtQuick
import QtQuick.Controls
import Kondor

ToolButton {
    id: root

    required property var browserWindow

    visible: UserProfiles.hasSeveralProfiles
    display: AbstractButton.TextBesideIcon
    text: UserProfiles.currentName
    icon.name: UserProfiles.currentIconName
    ToolTip.visible: hovered
    ToolTip.text: qsTr("Profile: %1").arg(UserProfiles.currentName)
    ToolTip.delay: 600
    Accessible.name: ToolTip.text
    onClicked: profilesMenu.popup(root, 0, root.height)

    ProfilesMenu {
        id: profilesMenu
        browserWindow: root.browserWindow
    }
}
