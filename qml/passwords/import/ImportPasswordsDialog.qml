import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Dialog {
    id: root

    property var info: ({})
    readonly property string error: root.info.error ? root.info.error : ""
    readonly property string fileName: root.info.fileName ? root.info.fileName : ""
    readonly property int newCount: root.info.newCount ? root.info.newCount : 0
    readonly property int identicalCount: root.info.identicalCount ? root.info.identicalCount : 0
    readonly property int conflictCount: root.info.conflictCount ? root.info.conflictCount : 0
    readonly property int conflictSites: root.info.conflictSites ? root.info.conflictSites : 0
    readonly property int skippedNoSite: root.info.skippedNoSite ? root.info.skippedNoSite : 0
    readonly property int skippedNoCredentials: root.info.skippedNoCredentials ? root.info.skippedNoCredentials : 0
    readonly property int skippedNotLogin: root.info.skippedNotLogin ? root.info.skippedNotLogin : 0
    readonly property int skippedTotal: root.skippedNoSite + root.skippedNoCredentials + root.skippedNotLogin
    readonly property int importCount: root.newCount + (replaceCheck.checked ? root.conflictCount : 0)

    readonly property string errorText: {
        switch (root.error) {
        case "notPasswordExport":
            return qsTr("“%1” is not a password export: it has no website, username and password columns.").arg(root.fileName)
        case "empty":
            return qsTr("“%1” has no passwords to import.").arg(root.fileName)
        case "unreadable":
            return qsTr("“%1” could not be read.").arg(root.fileName)
        case "tooLarge":
            return qsTr("“%1” is too large to be a password export.").arg(root.fileName)
        case "walletUnavailable":
            return qsTr("KWallet is not available, so passwords cannot be imported.")
        }
        return ""
    }

    readonly property string skippedText: {
        const reasons = []
        if (root.skippedNoSite > 0)
            reasons.push(qsTr("%n without an https:// website", "", root.skippedNoSite))
        if (root.skippedNoCredentials > 0)
            reasons.push(qsTr("%n without a username or password", "", root.skippedNoCredentials))
        if (root.skippedNotLogin > 0)
            reasons.push(qsTr("%n that are not logins", "", root.skippedNotLogin))
        return qsTr("%n entries: %1", "", root.skippedTotal).arg(reasons.join(", "))
    }

    function openFor(result) {
        replaceCheck.checked = false
        root.info = result
        root.open()
    }

    function submit() {
        PasswordStore.commitImport(replaceCheck.checked)
        root.close()
    }

    anchors.centerIn: parent
    width: Kirigami.Units.gridUnit * 34
    modal: true
    dim: true
    closePolicy: Popup.CloseOnEscape
    title: qsTr("Import Passwords")

    onClosed: {
        PasswordStore.cancelImport()
        root.info = ({})
    }

    footer: DialogButtonBox {
        Button {
            visible: root.error === ""
            enabled: root.importCount > 0
            text: qsTr("Import %n Password(s)", "", root.importCount)
            icon.name: "document-import"
            DialogButtonBox.buttonRole: DialogButtonBox.ActionRole
            onClicked: root.submit()
        }
        Button {
            text: root.error === "" ? qsTr("Cancel") : qsTr("Close")
            icon.name: root.error === "" ? "dialog-cancel" : "dialog-close"
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
        }
        onRejected: root.close()
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: root.error !== ""
            type: Kirigami.MessageType.Error
            text: root.errorText
        }

        Kirigami.FormLayout {
            Layout.fillWidth: true
            visible: root.error === ""

            Label {
                Kirigami.FormData.label: qsTr("File:")
                Layout.fillWidth: true
                elide: Text.ElideMiddle
                text: root.info.format && root.info.format !== "CSV"
                      ? qsTr("%1 (%2)").arg(root.fileName).arg(root.info.format)
                      : root.fileName
            }

            Label {
                Kirigami.FormData.label: qsTr("New:")
                visible: root.newCount > 0
                text: qsTr("%n password(s)", "", root.newCount)
            }

            Label {
                Kirigami.FormData.label: qsTr("Already saved:")
                visible: root.identicalCount > 0
                text: qsTr("%n password(s) are identical and are skipped", "", root.identicalCount)
            }

            Label {
                Kirigami.FormData.label: qsTr("Different:")
                visible: root.conflictCount > 0
                text: qsTr("%n site(s) already have a different saved password", "", root.conflictSites)
            }

            CheckBox {
                id: replaceCheck
                visible: root.conflictCount > 0
                text: qsTr("Replace them with the imported passwords")
            }

            Label {
                Kirigami.FormData.label: qsTr("Not imported:")
                visible: root.skippedTotal > 0
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: root.skippedText
            }
        }
    }
}
