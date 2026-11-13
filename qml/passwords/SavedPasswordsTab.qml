import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ColumnLayout {
    id: root

    required property bool walletDenied
    required property bool offerToSave
    required property ImportResult importResult
    required property RevealedPasswords revealed
    signal offerToSaveToggled(bool checked)
    signal addRequested
    signal importRequested
    signal deleteRequested(string origin, string username)

    function rebuild() {
        list.rebuild()
    }

    function showLogin(origin, username) {
        filterField.text = ""
        list.rebuild()
        list.select(origin, username)
    }

    spacing: Kirigami.Units.largeSpacing

    Kirigami.InlineMessage {
        Layout.fillWidth: true
        visible: root.walletDenied
        type: Kirigami.MessageType.Warning
        text: qsTr("KWallet is disabled or access to it was denied, so passwords cannot be saved or filled.")
        actions: [
            Kirigami.Action {
                text: qsTr("Try Again")
                icon.name: "view-refresh"
                onTriggered: PasswordStore.retry()
            }
        ]
    }

    ImportPreparingRow { fileName: root.importResult.name }

    ImportProgressMessage { Layout.fillWidth: true }

    ImportMessage { result: root.importResult }

    CheckBox {
        id: offerCheck
        enabled: !root.walletDenied
        text: qsTr("Offer to save passwords")
        onToggled: root.offerToSaveToggled(checked)
    }

    Binding {
        target: offerCheck
        property: "checked"
        value: root.offerToSave
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing

        TextField {
            id: filterField
            Layout.fillWidth: true
            enabled: !root.walletDenied
            placeholderText: qsTr("Filter by site or username…")
        }

        Button {
            text: qsTr("Add Password…")
            icon.name: "list-add"
            enabled: !root.walletDenied
            onClicked: root.addRequested()
        }

        Button {
            text: qsTr("Import…")
            icon.name: "document-import"
            enabled: !root.walletDenied && !PasswordStore.importPreparing && !PasswordStore.importRunning
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Import passwords from a CSV file")
            ToolTip.delay: 600
            onClicked: root.importRequested()
        }
    }

    SavedPasswordsList {
        id: list
        Layout.fillWidth: true
        Layout.fillHeight: true
        walletDenied: root.walletDenied
        filter: filterField.text
        revealed: root.revealed
        onAddRequested: root.addRequested()
        onDeleteRequested: function(origin, username) { root.deleteRequested(origin, username) }
    }
}
