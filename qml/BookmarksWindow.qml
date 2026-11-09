pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// "Manage Bookmarks" window (Ctrl+Shift+O): folder tree on the left, the items
// of the selected folder on the right. Created on demand in Main.qml. Visuals
// follow the 02b-bookmarks-manager.qml prototype.
ApplicationWindow {
    id: root
    width: 820
    height: 540
    title: qsTr("Manage Bookmarks")
    visible: false

    required property TabModel tabModel

    property var selectedFolderId: BookmarkManager.otherFolderId()
    property string filter: ""

    // Rebuilt whenever a bookmark write bumps the revision.
    property var folders: {
        const revision = BookmarkManager.revision
        return revision >= 0 ? BookmarkManager.folders : []
    }

    property var itemModel: {
        const revision = BookmarkManager.revision
        return revision >= 0 ? BookmarkManager.modelForFolder(root.selectedFolderId) : null
    }

    onItemModelChanged: {
        if (root.itemModel)
            root.itemModel.filter = root.filter
    }

    onFilterChanged: {
        if (root.itemModel)
            root.itemModel.filter = root.filter
    }

    onClosing: function(close) {
        // Do not destroy: just hide, so it reopens quickly.
        close.accepted = false
        root.visible = false
    }

    function showWindow() {
        root.visible = true
        root.raise()
        root.requestActivate()
    }

    function selectedInfo() {
        const revision = BookmarkManager.revision
        return revision >= 0 ? BookmarkManager.bookmark(root.selectedFolderId) : {}
    }

    function openBookmark(url, background) {
        if (!url)
            return
        const tab = root.tabModel.currentTab
        if (!tab) {
            root.tabModel.addTab(false, url)
        } else if (background) {
            // A new tab keeps the current mode: private stays private.
            const profile = tab.isPrivate ? ProfileManager.createPrivateProfile()
                                          : ProfileManager.defaultProfile()
            root.tabModel.addTabWithProfile(profile, url, true)
        } else {
            tab.navigateTo(url)
        }
    }

    // True when the right-hand list has a current row: the toolbar actions
    // then apply to that bookmark/folder instead of the selected folder.
    function hasItemSelection() {
        return root.itemModel && itemList.currentIndex >= 0
    }

    function currentItemInfo() {
        if (!root.hasItemSelection())
            return {}
        const revision = BookmarkManager.revision
        return revision >= 0 ? BookmarkManager.bookmark(root.itemModel.idAt(itemList.currentIndex))
                             : {}
    }

    // The item the toolbar actions apply to: the row of the right-hand list
    // when there is one, the selected folder otherwise.
    function actionTarget() {
        return root.hasItemSelection() ? root.currentItemInfo() : root.selectedInfo()
    }

    function actionIsFolder() {
        return root.hasItemSelection() ? root.currentItemInfo().isFolder : true
    }

    function moveSelected(delta) {
        const info = root.actionTarget()
        if (!info.id || info.special)
            return
        const parentId = root.hasItemSelection() ? root.selectedFolderId : info.parentId
        BookmarkManager.move(info.id, parentId, info.position + delta)
        if (root.hasItemSelection())
            itemList.currentIndex =
                Math.max(0, Math.min(info.position + delta, root.itemModel.count - 1))
    }

    function openCurrentItem() {
        if (!root.itemModel || itemList.currentIndex < 0)
            return
        if (root.itemModel.isFolderAt(itemList.currentIndex))
            root.selectedFolderId = root.itemModel.idAt(itemList.currentIndex)
        else
            root.openBookmark(root.itemModel.urlAt(itemList.currentIndex))
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        ToolBar {
            Layout.fillWidth: true

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 4
                anchors.rightMargin: 4
                spacing: 4

                ToolButton {
                    text: qsTr("New Folder")
                    icon.name: "folder-new"
                    onClicked: newFolderDialog.open()
                }
                ToolButton {
                    text: qsTr("Rename")
                    icon.name: "edit-rename"
                    enabled: root.hasItemSelection() || root.selectedFolderId > 0
                    onClicked: {
                        const target = root.actionTarget()
                        if (!target.id)
                            return
                        renameDialog.targetId = target.id
                        renameDialog.targetIsFolder = root.actionIsFolder()
                        renameDialog.targetTitle = target.title
                        renameDialog.open()
                    }
                }
                ToolButton {
                    text: qsTr("Delete")
                    icon.name: "edit-delete"
                    enabled: root.hasItemSelection()
                             || (root.selectedFolderId > 0 && !root.selectedInfo().special)
                    onClicked: {
                        const target = root.actionTarget()
                        if (!target.id)
                            return
                        deleteDialog.targetId = target.id
                        deleteDialog.targetIsFolder = root.actionIsFolder()
                        deleteDialog.open()
                    }
                }
                ToolButton {
                    display: AbstractButton.IconOnly
                    icon.name: "go-up"
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Move Up")
                    ToolTip.delay: 600
                    enabled: (root.hasItemSelection() || !root.selectedInfo().special)
                             && root.actionTarget().id > 0
                    onClicked: root.moveSelected(-1)
                }
                ToolButton {
                    display: AbstractButton.IconOnly
                    icon.name: "go-down"
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Move Down")
                    ToolTip.delay: 600
                    enabled: (root.hasItemSelection() || !root.selectedInfo().special)
                             && root.actionTarget().id > 0
                    onClicked: root.moveSelected(1)
                }

                Item { Layout.fillWidth: true }

                ToolButton {
                    text: qsTr("Import from HTML…")
                    icon.name: "document-import"
                    onClicked: importDialog.open()
                }

                TextField {
                    id: searchField
                    Layout.preferredWidth: Kirigami.Units.gridUnit * 14
                    placeholderText: qsTr("Search bookmarks…")
                    onTextChanged: searchTimer.restart()
                }
            }
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ScrollView {
                SplitView.preferredWidth: 240
                Kirigami.Theme.colorSet: Kirigami.Theme.View
                Kirigami.Theme.inherit: false
                background: Rectangle { color: Kirigami.Theme.backgroundColor }

                ListView {
                    id: folderList
                    clip: true
                    model: root.folders

                    delegate: ItemDelegate {
                        id: folderEntry

                        required property var modelData
                        required property int index

                        width: ListView.view.width
                        highlighted: folderEntry.modelData.id === root.selectedFolderId
                        icon.name: "folder"
                        text: folderEntry.modelData.title
                        leftPadding: 10 + folderEntry.modelData.depth * 18

                        onClicked: root.selectedFolderId = folderEntry.modelData.id
                    }
                }
            }

            ScrollView {
                Kirigami.Theme.colorSet: Kirigami.Theme.View
                Kirigami.Theme.inherit: false
                background: Rectangle { color: Kirigami.Theme.backgroundColor }

                ListView {
                    id: itemList
                    clip: true
                    model: root.itemModel
                    focus: true

                    Keys.onReturnPressed: root.openCurrentItem()
                    Keys.onEnterPressed: root.openCurrentItem()

                    delegate: ItemDelegate {
                        id: itemEntry

                        required property int index
                        required property int id
                        required property string title
                        required property string url
                        required property bool isFolder

                        width: ListView.view.width
                        highlighted: ListView.isCurrentItem

                        contentItem: RowLayout {
                            spacing: Kirigami.Units.largeSpacing

                            Kirigami.Icon {
                                source: itemEntry.isFolder ? "folder" : "internet-web-browser"
                                Layout.preferredWidth: 22
                                Layout.preferredHeight: 22
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 0

                                Label {
                                    Layout.fillWidth: true
                                    text: itemEntry.title.length ? itemEntry.title : itemEntry.url
                                    elide: Text.ElideRight
                                    font.bold: true
                                }

                                Label {
                                    visible: !itemEntry.isFolder
                                    Layout.fillWidth: true
                                    text: itemEntry.url
                                    elide: Text.ElideRight
                                    color: itemEntry.highlighted
                                           ? Kirigami.Theme.highlightedTextColor
                                           : Kirigami.Theme.disabledTextColor
                                    font: Kirigami.Theme.smallFont
                                }
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.LeftButton | Qt.MiddleButton

                            onDoubleClicked: function(mouse) {
                                if (mouse.button === Qt.LeftButton)
                                    root.openCurrentItem()
                            }
                            onClicked: function(mouse) {
                                itemList.currentIndex = itemEntry.index
                                itemList.forceActiveFocus()
                                if (itemEntry.isFolder) {
                                    if (mouse.button === Qt.LeftButton)
                                        root.selectedFolderId = itemEntry.id
                                    return
                                }
                                if (mouse.button === Qt.MiddleButton) {
                                    root.openBookmark(itemEntry.url, true)
                                    return
                                }
                                if (BookmarkManager.ctrlPressed()) {
                                    root.openBookmark(itemEntry.url, true)
                                    return
                                }
                                // Qt.styleHints is typed QObject* in the QML
                                // global object, but returns a QStyleHints at
                                // runtime.
                                // qmllint disable missing-property
                                if (Qt.styleHints.singleClickActivation)
                                    root.openBookmark(itemEntry.url, false)
                            }
                        }
                    }
                }
            }
        }
    }

    Timer {
        id: searchTimer
        interval: 200
        onTriggered: root.filter = searchField.text
    }

    Dialog {
        id: newFolderDialog
        title: qsTr("New Folder")
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        anchors.centerIn: parent

        onOpened: newFolderField.forceActiveFocus()

        TextField {
            id: newFolderField
            //: Default name of a new bookmark folder
            placeholderText: qsTr("New Folder")
            width: Kirigami.Units.gridUnit * 18
        }

        onAccepted: {
            const id = BookmarkManager.addFolder(newFolderField.text, root.selectedFolderId)
            if (id > 0)
                root.selectedFolderId = id
            newFolderField.text = ""
        }
        onRejected: newFolderField.text = ""
    }

    Dialog {
        id: renameDialog
        property var targetId: -1
        property bool targetIsFolder: true
        property string targetTitle: ""
        title: renameDialog.targetIsFolder ? qsTr("Rename Folder") : qsTr("Rename Bookmark")
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        anchors.centerIn: parent

        onOpened: {
            renameField.text = renameDialog.targetTitle
            renameField.selectAll()
            renameField.forceActiveFocus()
        }

        TextField {
            id: renameField
            width: Kirigami.Units.gridUnit * 18
        }

        onAccepted: {
            if (renameDialog.targetId > 0)
                BookmarkManager.rename(renameDialog.targetId, renameField.text)
        }
    }

    MessageDialog {
        id: deleteDialog
        property var targetId: -1
        property bool targetIsFolder: true
        title: deleteDialog.targetIsFolder ? qsTr("Delete Folder") : qsTr("Delete Bookmark")
        text: deleteDialog.targetIsFolder
              ? qsTr("Delete this folder and everything in it?")
              : qsTr("Delete this bookmark?")
        buttons: MessageDialog.Yes | MessageDialog.No
        onAccepted: {
            const info = BookmarkManager.bookmark(deleteDialog.targetId)
            if (!info.id)
                return
            BookmarkManager.remove(info.id)
            // Deleting the selected folder moves the selection to its parent.
            if (!deleteDialog.targetIsFolder)
                return
            root.selectedFolderId = info.parentId > 0 ? info.parentId : BookmarkManager.otherFolderId()
        }
    }

    FileDialog {
        id: importDialog
        title: qsTr("Import Bookmarks")
        fileMode: FileDialog.OpenFile
        nameFilters: ["HTML (*.html *.htm)"]
        onAccepted: BookmarkManager.importHtml(selectedFile)
    }
}
