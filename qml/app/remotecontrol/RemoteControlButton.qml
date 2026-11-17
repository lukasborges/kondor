import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor

ToolButton {
    id: root

    required property var browserWindow

    readonly property int connectionCount: RemoteControl.connections.count

    function describeConnections() {
        if (connectionCount > 1)
            return qsTr("%n agents are controlling Kondor", "", connectionCount)
        if (RemoteControl.connections.firstName === "")
            return qsTr("An automation tool is controlling Kondor")
        return qsTr("%1 is controlling Kondor").arg(RemoteControl.connections.firstName)
    }

    visible: connectionCount > 0
    display: AbstractButton.IconOnly
    focusPolicy: Qt.TabFocus
    icon.name: "automated-tasks"
    icon.color: Kirigami.Theme.neutralTextColor
    checked: popup.opened
    ToolTip.visible: hovered
    ToolTip.text: describeConnections()
    ToolTip.delay: 600
    Accessible.name: ToolTip.text
    onClicked: popup.opened ? popup.close() : popup.open()
    onVisibleChanged: if (!visible) popup.close()

    RemoteControlPopup {
        id: popup
        browserWindow: root.browserWindow
        x: root.width - width
        y: root.height
    }
}
