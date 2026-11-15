import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

RowLayout {
    id: root

    required property var extension

    signal settingsRequested(string extensionId)

    Layout.fillWidth: true

    Item { Layout.fillWidth: true }

    Button {
        text: qsTr("Settings…")
        icon.name: "configure"
        flat: true
        onClicked: root.settingsRequested(root.extension.id)
    }
}
