import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor

ToolButton {
    id: root

    required property var browserWindow

    visible: RemoteControl.active
    display: AbstractButton.IconOnly
    icon.name: "automated-tasks"
    icon.color: Kirigami.Theme.neutralTextColor
    checked: popup.opened
    ToolTip.visible: hovered
    ToolTip.text: qsTr("Remote control is on")
    ToolTip.delay: 600
    Accessible.name: ToolTip.text
    onClicked: popup.opened ? popup.close() : popup.open()

    RemoteControlPopup {
        id: popup
        browserWindow: root.browserWindow
        x: root.width - width
        y: root.height
    }
}
