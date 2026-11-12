import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Dialog {
    id: root

    signal saved(string origin, string username)

    readonly property string origin: PasswordStore.originFromInput(websiteField.text)
    readonly property bool siteInvalid: websiteField.text.trim() !== "" && root.origin === ""
    readonly property bool duplicate: root.origin !== "" && usernameField.text !== ""
        && PasswordStore.contains(root.origin, usernameField.text)
    readonly property bool valid: root.origin !== "" && usernameField.text !== ""
        && passwordField.text !== ""
    property bool saveFailed: false

    function clear() {
        websiteField.text = ""
        usernameField.text = ""
        passwordField.text = ""
        root.saveFailed = false
    }

    function submit() {
        if (!root.valid)
            return
        if (PasswordStore.save(root.origin, usernameField.text, passwordField.text)) {
            const origin = root.origin
            const username = usernameField.text
            root.close()
            root.saved(origin, username)
        } else {
            root.saveFailed = true
        }
    }

    anchors.centerIn: parent
    width: Kirigami.Units.gridUnit * 24
    modal: true
    dim: true
    closePolicy: Popup.CloseOnEscape
    title: qsTr("Add Password")
    standardButtons: Dialog.Save | Dialog.Cancel

    onAboutToShow: websiteField.forceActiveFocus()
    onClosed: root.clear()
    Component.onCompleted: {
        const save = standardButton(Dialog.Save)
        save.DialogButtonBox.buttonRole = DialogButtonBox.ActionRole
        save.enabled = Qt.binding(function() { return root.valid })
        save.clicked.connect(root.submit)
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.FormLayout {
            Layout.fillWidth: true

            TextField {
                id: websiteField
                Kirigami.FormData.label: qsTr("Website:")
                Layout.fillWidth: true
                placeholderText: qsTr("https://example.com")
                onTextChanged: root.saveFailed = false
                onAccepted: root.submit()
            }

            TextField {
                id: usernameField
                Kirigami.FormData.label: qsTr("Username:")
                Layout.fillWidth: true
                onTextChanged: root.saveFailed = false
                onAccepted: root.submit()
            }

            Kirigami.PasswordField {
                id: passwordField
                Kirigami.FormData.label: qsTr("Password:")
                Layout.fillWidth: true
                onTextChanged: root.saveFailed = false
                onAccepted: root.submit()
            }
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: root.saveFailed || root.siteInvalid || root.duplicate
            type: root.saveFailed || root.siteInvalid ? Kirigami.MessageType.Error
                                                      : Kirigami.MessageType.Warning
            text: root.saveFailed
                  ? qsTr("The password could not be saved to KWallet.")
                  : root.siteInvalid
                    ? qsTr("Passwords can only be saved for https:// sites and localhost.")
                    : qsTr("A password for %1 on %2 is already saved. Saving replaces it.")
                          .arg(usernameField.text).arg(PasswordStore.hostOfOrigin(root.origin))
        }
    }
}
