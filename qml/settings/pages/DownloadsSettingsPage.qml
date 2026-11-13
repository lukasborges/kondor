import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import org.kde.kirigami as Kirigami
import Kondor

ScrollView {
    id: root

    required property SettingsDraft draft

    contentWidth: availableWidth
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    LocalPath { id: localPath }

    ColumnLayout {
        width: root.availableWidth
        spacing: Kirigami.Units.largeSpacing

        Kirigami.FormLayout {
            Layout.fillWidth: true

            RowLayout {
                Kirigami.FormData.label: qsTr("Save files to:")

                TextField {
                    Layout.preferredWidth: Kirigami.Units.gridUnit * 16
                    text: root.draft.downloadDirectory
                    readOnly: true
                    selectByMouse: true
                }

                Button {
                    text: qsTr("Choose…")
                    icon.name: "document-open-folder"
                    onClicked: downloadFolderDialog.open()
                }
            }

            CheckBox {
                id: askCheck
                text: qsTr("Ask where to save each file")
                onToggled: root.draft.askWhereToSave = checked
            }

            Binding {
                target: askCheck
                property: "checked"
                value: root.draft.askWhereToSave
            }
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: !Settings.downloadDirectoryValid
            type: Kirigami.MessageType.Warning
            text: qsTr("The selected folder no longer exists. Downloads are saved to %1.")
                      .arg(Settings.downloadDirectory)
        }

        Item { Layout.fillHeight: true }
    }

    FolderDialog {
        id: downloadFolderDialog
        title: qsTr("Choose Download Folder")
        currentFolder: "file://" + root.draft.downloadDirectory
        onAccepted: root.draft.downloadDirectory = localPath.fromUrl(selectedFolder)
    }
}
