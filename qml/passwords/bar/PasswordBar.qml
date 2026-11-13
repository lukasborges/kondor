import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

InlineBar {
    id: root

    property Tab tab: null
    readonly property string kind: tab ? tab.passwords.prompt : ""

    visible: kind !== ""

    function escapeHtml(text) {
        return String(text ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
    }

    Kirigami.Icon {
        source: root.kind === "walletUnavailable" ? "dialog-warning" : "dialog-password"
        Layout.preferredWidth: Kirigami.Units.iconSizes.small
        Layout.preferredHeight: Kirigami.Units.iconSizes.small
    }

    Label {
        Layout.fillWidth: true
        elide: Text.ElideRight
        textFormat: Text.RichText
        text: root.kind === "save"
              ? qsTr("Save the password for <b>%1</b> on <b>%2</b>?")
                    .arg(root.escapeHtml(root.tab.passwords.promptUsername))
                    .arg(root.escapeHtml(root.tab.passwords.promptHost))
              : root.kind === "walletUnavailable"
                ? qsTr("KWallet is disabled or access to it was denied, so passwords cannot be saved or filled.")
                : ""
    }

    Button {
        visible: root.kind === "save"
        text: qsTr("Save")
        icon.name: "document-save"
        onClicked: root.tab.passwords.savePending()
    }

    Button {
        text: root.kind === "save" ? qsTr("Not Now") : qsTr("Close")
        icon.name: root.kind === "save" ? "dialog-cancel" : "window-close"
        onClicked: root.tab.passwords.dismissPrompt()
    }

    Button {
        visible: root.kind === "save"
        text: qsTr("Never for This Site")
        icon.name: "edit-delete"
        onClicked: root.tab.passwords.neverSavePending()
    }
}
