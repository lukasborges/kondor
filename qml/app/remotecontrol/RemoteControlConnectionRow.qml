import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

RowLayout {
    id: root

    required property int index
    required property string name
    required property date connectedSince
    required property bool canDisconnect

    readonly property string displayName: name === "" ? qsTr("Automation tool") : name

    spacing: Kirigami.Units.largeSpacing

    Kirigami.Icon {
        source: "dialog-scripts"
        Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
        Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
    }

    ColumnLayout {
        spacing: 0
        Layout.fillWidth: true

        Label {
            text: root.displayName
            font.bold: true
            elide: Text.ElideRight
            Layout.fillWidth: true
        }

        Label {
            text: qsTr("Connected since %1").arg(root.connectedSince.toLocaleTimeString(Qt.locale(), Locale.ShortFormat))
            color: Kirigami.Theme.disabledTextColor
            Layout.fillWidth: true
            elide: Text.ElideRight
        }
    }

    ToolButton {
        visible: root.canDisconnect
        display: AbstractButton.IconOnly
        icon.name: "network-disconnect"
        ToolTip.visible: hovered
        ToolTip.text: qsTr("Disconnect")
        ToolTip.delay: 600
        Accessible.name: qsTr("Disconnect %1").arg(root.displayName)
        onClicked: RemoteControl.connections.disconnectAt(root.index)
    }
}
