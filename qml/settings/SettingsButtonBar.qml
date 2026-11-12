import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: root

    required property bool modified
    required property bool defaultsEnabled

    signal defaultsClicked()
    signal okClicked()
    signal applyClicked()
    signal cancelClicked()

    Layout.fillWidth: true
    spacing: 0

    Kirigami.Separator { Layout.fillWidth: true }

    RowLayout {
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.smallSpacing

        Button {
            text: qsTr("Defaults")
            icon.name: "document-revert"
            enabled: root.defaultsEnabled
            onClicked: root.defaultsClicked()
        }

        Item { Layout.fillWidth: true }

        Button {
            text: qsTr("OK")
            icon.name: "dialog-ok"
            highlighted: true
            onClicked: root.okClicked()
        }

        Button {
            text: qsTr("Apply")
            icon.name: "dialog-ok-apply"
            enabled: root.modified
            onClicked: root.applyClicked()
        }

        Button {
            text: qsTr("Cancel")
            icon.name: "dialog-cancel"
            onClicked: root.cancelClicked()
        }
    }
}
