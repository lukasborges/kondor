import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

RowLayout {
    id: root

    required property var extension
    required property bool isPinned
    required property bool isPrivate

    signal settingsRequested(string extensionId)

    Layout.fillWidth: true

    Button {
        objectName: "pinButton"
        visible: !root.isPrivate
        text: root.isPinned ? qsTr("Unpin from Toolbar") : qsTr("Pin to Toolbar")
        icon.name: root.isPinned ? "window-unpin" : "window-pin"
        flat: true
        onClicked: ExtensionManager.setPinned(root.extension.id, !root.isPinned)
    }

    Item { Layout.fillWidth: true }

    Button {
        text: qsTr("Settings…")
        icon.name: "configure"
        flat: true
        onClicked: root.settingsRequested(root.extension.id)
    }
}
