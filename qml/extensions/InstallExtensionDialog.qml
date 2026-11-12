import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// Confirmation before an extension is installed, from the catalog or from a
// .kondorext file: what it is, what it will be able to do and, for a file,
// that it does not come from the catalog. It shows the pending install of
// ExtensionManager; for a file that is not a valid extension it only shows the
// error.
Dialog {
    id: root

    readonly property var info: ExtensionManager.pendingInstall
    readonly property bool hasInfo: root.info.valid !== undefined
    readonly property bool isValid: root.info.valid === true
    readonly property bool replacing: root.isValid && root.info.installedVersion !== ""

    anchors.centerIn: parent
    width: Kirigami.Units.gridUnit * 26
    modal: true
    dim: true
    closePolicy: Popup.CloseOnEscape
    title: qsTr("Install Extension")
    visible: root.hasInfo

    onClosed: ExtensionManager.cancelInstall()

    footer: DialogButtonBox {
        Button {
            visible: root.isValid
            text: root.replacing ? qsTr("Replace") : qsTr("Install")
            icon.name: root.replacing ? "update-none" : "download"
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            onClicked: ExtensionManager.confirmInstall()
        }
        Button {
            text: root.isValid ? qsTr("Cancel") : qsTr("Close")
            icon.name: root.isValid ? "dialog-cancel" : "dialog-close"
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            onClicked: root.close()
        }
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: root.hasInfo && !root.isValid
            type: Kirigami.MessageType.Error
            text: qsTr("“%1” is not a valid Kondor extension: %2")
                      .arg(root.info.fileName ?? "").arg(root.info.error ?? "")
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: root.isValid && root.info.fromFile === true
            type: Kirigami.MessageType.Warning
            text: qsTr("This extension does not come from the Kondor extensions catalog. Only install extensions from people you trust.")
        }

        RowLayout {
            Layout.fillWidth: true
            visible: root.isValid
            spacing: Kirigami.Units.largeSpacing

            ExtensionIcon {
                source: root.info.iconSource ?? ""
                size: Kirigami.Units.iconSizes.large
            }

            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: root.replacing
                      ? qsTr("“%1” %2 is installed. Replace it with version %3?")
                            .arg(root.info.name).arg(root.info.installedVersion).arg(root.info.version)
                      : qsTr("Install “%1” %2 by %3?")
                            .arg(root.info.name ?? "").arg(root.info.version ?? "")
                            .arg(root.info.author ? root.info.author : qsTr("an unknown author"))
            }
        }

        Label {
            visible: root.isValid && (root.info.permissions ?? []).length > 0
            text: qsTr("It will be able to:")
        }

        Repeater {
            model: root.isValid ? root.info.permissions : []

            delegate: RowLayout {
                id: permissionRow
                required property var modelData
                Layout.leftMargin: Kirigami.Units.largeSpacing
                spacing: Kirigami.Units.smallSpacing

                Kirigami.Icon {
                    source: permissionRow.modelData.icon
                    Layout.preferredWidth: Kirigami.Units.iconSizes.small
                    Layout.preferredHeight: Kirigami.Units.iconSizes.small
                }
                Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: permissionRow.modelData.text
                }
            }
        }
    }
}
