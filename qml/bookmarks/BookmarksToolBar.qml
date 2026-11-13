import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ToolBar {
    id: root

    required property BookmarkSelection selection
    required property string filter

    readonly property bool canMove: root.filter.length === 0
        && (root.selection.hasItemSelection() || !root.selection.selectedInfo().special)
        && root.selection.actionTarget().id > 0

    signal newFolderRequested()
    signal renameRequested()
    signal deleteRequested()
    signal filterRequested(string text)

    Layout.fillWidth: true

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 4
        anchors.rightMargin: 4
        spacing: 4

        ToolButton {
            text: qsTr("New Folder")
            icon.name: "folder-new"
            onClicked: root.newFolderRequested()
        }
        ToolButton {
            text: qsTr("Rename")
            icon.name: "edit-rename"
            enabled: root.selection.hasItemSelection() || root.selection.folderId > 0
            onClicked: root.renameRequested()
        }
        ToolButton {
            text: qsTr("Delete")
            icon.name: "edit-delete"
            enabled: root.selection.hasItemSelection()
                     || (root.selection.folderId > 0 && !root.selection.selectedInfo().special)
            onClicked: root.deleteRequested()
        }
        ToolButton {
            display: AbstractButton.IconOnly
            icon.name: "go-up"
            ToolTip.visible: hovered
            Accessible.name: ToolTip.text
            ToolTip.text: qsTr("Move Up")
            ToolTip.delay: 600
            enabled: root.canMove
            onClicked: root.selection.moveSelected(-1)
        }
        ToolButton {
            objectName: "moveDownButton"
            display: AbstractButton.IconOnly
            icon.name: "go-down"
            ToolTip.visible: hovered
            Accessible.name: ToolTip.text
            ToolTip.text: qsTr("Move Down")
            ToolTip.delay: 600
            enabled: root.canMove
            onClicked: root.selection.moveSelected(1)
        }

        Item { Layout.fillWidth: true }

        ToolButton {
            text: qsTr("Import from HTML…")
            icon.name: "document-import"
            onClicked: importDialog.open()
        }

        TextField {
            id: searchField
            objectName: "bookmarkSearchField"
            Layout.preferredWidth: Kirigami.Units.gridUnit * 14
            placeholderText: qsTr("Search bookmarks…")
            onTextChanged: searchTimer.restart()
        }
    }

    Timer {
        id: searchTimer
        interval: 200
        onTriggered: root.filterRequested(searchField.text)
    }

    FileDialog {
        id: importDialog
        title: qsTr("Import Bookmarks")
        fileMode: FileDialog.OpenFile
        nameFilters: ["HTML (*.html *.htm)"]
        onAccepted: BookmarkManager.importHtml(selectedFile)
    }
}
