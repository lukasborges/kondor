pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kondor

ApplicationWindow {
    id: root
    width: 820
    height: 540
    title: qsTr("Manage Bookmarks")
    visible: false

    required property TabModel tabModel

    property alias selectedFolderId: bookmarkSelection.folderId
    property alias selectedItemId: bookmarkSelection.itemId
    property string filter: ""
    property var filteredModel: null

    property var folders: {
        const revision = BookmarkManager.revision
        return revision >= 0 ? BookmarkManager.folders : []
    }

    property var itemModel: {
        const revision = BookmarkManager.revision
        return revision >= 0 ? BookmarkManager.modelForFolder(root.selectedFolderId) : null
    }

    onItemModelChanged: {
        if (root.filteredModel && root.filteredModel !== root.itemModel)
            root.filteredModel.filter = ""
        root.filteredModel = root.itemModel
        root.applyFilter()
    }

    onFilterChanged: root.applyFilter()

    onClosing: function(close) {
        close.accepted = false
        root.visible = false
    }

    function applyFilter() {
        if (root.itemModel)
            root.itemModel.filter = root.filter
    }

    function showWindow() {
        root.visible = true
        root.raise()
        root.requestActivate()
    }

    BookmarkSelection {
        id: bookmarkSelection
        tabModel: root.tabModel
        itemModel: root.itemModel
        filter: root.filter
        onRowMoved: function(row) { itemPane.setCurrentRow(row) }
    }

    BookmarkFolderTree {
        id: bookmarkTree
        folders: root.folders
        onItemMoved: function(id, folderId) { bookmarkSelection.releaseItemMovedTo(id, folderId) }
    }

    BookmarkDragController {
        id: dragController
        preview: dragPreview
        folderTree: bookmarkTree
    }

    BookmarkDropTargets {
        id: bookmarkDropTargets
        drag: dragController
        folderList: folderPane.list
        itemList: itemPane.list
        folders: root.folders
        itemModel: root.itemModel
        filter: root.filter
        selectedFolderId: root.selectedFolderId
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        BookmarksToolBar {
            selection: bookmarkSelection
            filter: root.filter
            onNewFolderRequested: newFolderDialog.open()
            onRenameRequested: renameDialog.openFor(bookmarkSelection.actionTarget(), bookmarkSelection.actionIsFolder())
            onDeleteRequested: deleteDialog.openFor(bookmarkSelection.actionTarget(), bookmarkSelection.actionIsFolder())
            onFilterRequested: function(text) { root.filter = text }
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true

            BookmarkFolderPane {
                id: folderPane
                folders: root.folders
                selection: bookmarkSelection
                folderTree: bookmarkTree
                drag: dragController
                dropTargets: bookmarkDropTargets
            }

            BookmarkItemPane {
                id: itemPane
                itemModel: root.itemModel
                selection: bookmarkSelection
                folderTree: bookmarkTree
                drag: dragController
                dropTargets: bookmarkDropTargets
                contextMenu: itemContextMenu
            }
        }
    }

    BookmarkDragPreview {
        id: dragPreview
        drag: dragController
    }

    BookmarkItemContextMenu {
        id: itemContextMenu
        folderTree: bookmarkTree
    }

    NewBookmarkFolderDialog {
        id: newFolderDialog
        selection: bookmarkSelection
    }

    RenameBookmarkDialog { id: renameDialog }

    DeleteBookmarkDialog {
        id: deleteDialog
        selection: bookmarkSelection
    }
}
