import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Dialog {
    id: root

    required property BookmarkSelection selection

    title: qsTr("New Folder")
    standardButtons: Dialog.Ok | Dialog.Cancel
    modal: true
    anchors.centerIn: parent

    onOpened: newFolderField.forceActiveFocus()
    onAccepted: root.createFolder()
    onRejected: newFolderField.text = ""

    function createFolder() {
        const id = BookmarkManager.addFolder(newFolderField.text, root.selection.folderId)
        if (id > 0)
            root.selection.folderId = id
        newFolderField.text = ""
    }

    ColumnLayout {
        spacing: Kirigami.Units.smallSpacing

        Label {
            text: qsTr("Name:")
        }

        TextField {
            id: newFolderField
            //: Default name of a new bookmark folder
            placeholderText: qsTr("New Folder")
            Layout.fillWidth: true
            Layout.preferredWidth: Kirigami.Units.gridUnit * 18
            onAccepted: root.accept()
        }
    }
}
