import QtQuick
import QtQuick.Controls
import Kondor

Menu {
    id: root

    required property TabModel tabModel

    property var target: ({ id: -1, title: "", url: "", isFolder: false })
    property bool isOnItem: false
    property bool canAddPage: false
    property int bookmarkCount: 0

    readonly property bool isOnBookmark: root.isOnItem && !root.target.isFolder
    readonly property bool isOnFolder: root.isOnItem && root.target.isFolder

    signal openInTabRequested()
    signal openInWindowRequested()
    signal openAllRequested()
    signal addPageRequested()
    signal manageRequested()

    objectName: "barContextMenu"

    MenuItem {
        visible: root.isOnBookmark
        text: qsTr("Open in New Tab")
        icon.name: "tab-new"
        onTriggered: root.openInTabRequested()
    }
    MenuItem {
        visible: root.isOnBookmark
        text: qsTr("Open in New Window")
        icon.name: "window-new"
        onTriggered: root.openInWindowRequested()
    }
    MenuItem {
        visible: root.isOnFolder && root.bookmarkCount > 0
        text: qsTr("Open All in Tabs (%1)").arg(root.bookmarkCount)
        icon.name: "tab-new"
        onTriggered: root.openAllRequested()
    }
    MenuSeparator {
        visible: root.isOnBookmark
    }
    MenuItem {
        visible: root.isOnItem
        text: root.isOnFolder ? qsTr("Rename…") : qsTr("Edit…")
        icon.name: "document-edit"
        onTriggered: renameDialog.openFor(root.target, root.target.isFolder)
    }
    MenuItem {
        visible: root.isOnItem
        text: qsTr("Delete")
        icon.name: "edit-delete"
        onTriggered: deleteDialog.openFor(root.target, root.target.isFolder)
    }
    MenuItem {
        visible: !root.isOnItem && root.canAddPage
        text: qsTr("Add This Page")
        icon.name: "bookmark-new"
        onTriggered: root.addPageRequested()
    }
    MenuItem {
        visible: !root.isOnItem
        text: qsTr("Manage Bookmarks…")
        icon.name: "bookmarks-organize"
        onTriggered: root.manageRequested()
    }

    RenameBookmarkDialog {
        id: renameDialog
        parent: Overlay.overlay
    }

    DeleteBookmarkDialog {
        id: deleteDialog
        selection: BookmarkSelection {
            tabModel: root.tabModel
            itemModel: null
            filter: ""
        }
    }
}
