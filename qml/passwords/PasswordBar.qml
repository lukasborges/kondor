import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// Inline prompt of the password manager: offers to save the login just
// submitted in this tab, or says once that KWallet is unavailable. It belongs
// to the tab, so switching tabs keeps it with the page.
InlineBar {
    id: root

    property Tab tab: null
    readonly property string kind: tab ? tab.passwordPrompt : ""

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
                    .arg(root.escapeHtml(root.tab.passwordPromptUsername))
                    .arg(root.escapeHtml(root.tab.passwordPromptHost))
              : root.kind === "walletUnavailable"
                ? qsTr("KWallet is disabled or access to it was denied, so passwords cannot be saved or filled.")
                : ""
    }

    Button {
        visible: root.kind === "save"
        text: qsTr("Save")
        icon.name: "document-save"
        onClicked: root.tab.savePendingPassword()
    }

    Button {
        text: root.kind === "save" ? qsTr("Not Now") : qsTr("Close")
        icon.name: root.kind === "save" ? "dialog-cancel" : "window-close"
        onClicked: root.tab.dismissPasswordPrompt()
    }

    Button {
        visible: root.kind === "save"
        text: qsTr("Never for This Site")
        icon.name: "edit-delete"
        onClicked: root.tab.neverSavePendingPassword()
    }
}
