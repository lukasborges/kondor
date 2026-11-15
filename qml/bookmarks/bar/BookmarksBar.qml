pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ToolBar {
    id: root

    required property TabModel tabModel

    property int visibleCount: 0

    readonly property var toolbarId: BookmarkManager.toolbarFolderId()

    signal manageBookmarksRequested()

    function countThatFit(available) {
        let used = 0
        for (let i = 0; i < items.count; ++i) {
            used += items.itemAt(i).implicitWidth + row.spacing
            if (used - row.spacing > available)
                return i
        }
        return items.count
    }

    function updateVisibleCount() {
        if (items.count === 0 || items.itemAt(items.count - 1) === null)
            return
        const all = root.countThatFit(row.width)
        const reserved = overflowButton.implicitWidth + row.spacing
        root.visibleCount = all === items.count ? all : root.countThatFit(row.width - reserved)
    }

    function activate(button) {
        if (!button.isFolder)
            return actions.openBookmark(button.url, BookmarkManager.ctrlPressed())
        folderMenu.folderId = button.id
        folderMenu.canAddPage = actions.canAddPageTo(button.id)
        folderMenu.popup(button, 0, button.height)
    }

    function showContextMenu(button) {
        contextMenu.target = { id: button.id, title: button.title, url: button.url, isFolder: button.isFolder }
        contextMenu.isOnItem = true
        contextMenu.bookmarkCount = button.isFolder ? actions.bookmarksIn(button.id).length : 0
        contextMenu.popup(button, 0, button.height)
    }

    function isOverEmptySpace(point) {
        const hit = row.childAt(root.mapToItem(row, point).x, root.mapToItem(row, point).y)
        return hit === null || hit === spacer
    }

    function showBarContextMenu(point) {
        if (!root.isOverEmptySpace(point))
            return
        contextMenu.isOnItem = false
        contextMenu.canAddPage = actions.canAddPageTo(root.toolbarId)
        contextMenu.popup()
    }

    visible: Settings.showBookmarksBar
    Kirigami.Theme.colorSet: Kirigami.Theme.Window
    Kirigami.Theme.inherit: false
    position: ToolBar.Header
    onVisibleChanged: Qt.callLater(root.updateVisibleCount)

    RowLayout {
        id: row

        anchors.fill: parent
        anchors.leftMargin: 4
        anchors.rightMargin: 4
        spacing: 2
        onWidthChanged: Qt.callLater(root.updateVisibleCount)

        Repeater {
            id: items

            model: BookmarkManager.toolbarModel
            onCountChanged: Qt.callLater(root.updateVisibleCount)

            delegate: BookmarksBarItem {
                id: button

                visible: button.index < root.visibleCount
                drag: dragController
                onImplicitWidthChanged: Qt.callLater(root.updateVisibleCount)
                onClicked: root.activate(button)
                onBackgroundOpenRequested: actions.openBookmark(button.url, true)
                onContextMenuRequested: root.showContextMenu(button)
            }
        }

        Item {
            id: spacer
            Layout.fillWidth: true
        }

        BookmarksBarOverflow {
            id: overflowButton

            visible: root.visibleCount < items.count
            skippedCount: root.visibleCount
            onBookmarkActivated: function(url, background) { actions.openBookmark(url, background) }
        }
    }

    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: function(eventPoint) { root.showBarContextMenu(eventPoint.position) }
    }

    DropArea {
        anchors.fill: row
        keys: ["kondor/bookmark"]
        onEntered: function(drag) { dropTargets.updateMoveDrop(drag.x) }
        onPositionChanged: function(drag) { dropTargets.updateMoveDrop(drag.x) }
        onExited: dragController.clearDropTarget()
        onDropped: dropTargets.completeMove()
    }

    BookmarksBarLinkDrop {
        anchors.fill: row
        enabled: actions.canAddBookmarks
        targets: dropTargets
    }

    Rectangle {
        visible: dragController.dropPosition >= 0
        x: row.x + dropTargets.indicatorX() - 1
        y: (root.height - height) / 2
        width: 2
        height: Kirigami.Units.iconSizes.smallMedium + Kirigami.Units.smallSpacing
        radius: 1
        color: Kirigami.Theme.highlightColor
    }

    BookmarkDragPreview {
        id: dragPreview
        drag: dragController
    }

    BookmarksBarActions {
        id: actions
        tabModel: root.tabModel
    }

    BookmarkDragController {
        id: dragController
        preview: dragPreview
        folderTree: folderTree
    }

    BookmarkFolderTree {
        id: folderTree
        folders: BookmarkManager.folders
    }

    BookmarksBarDropTargets {
        id: dropTargets
        drag: dragController
        folderTree: folderTree
        items: items
        visibleCount: root.visibleCount
    }

    BookmarkMenu {
        id: folderMenu
        showFolderActions: true
        onBookmarkActivated: function(url, background) { actions.openBookmark(url, background) }
        onOpenAllRequested: actions.openAllIn(folderMenu.folderId)
        onAddPageRequested: actions.addPageTo(folderMenu.folderId)
    }

    BookmarksBarContextMenu {
        id: contextMenu
        tabModel: root.tabModel
        onOpenInTabRequested: actions.openInNewTab(contextMenu.target.url, false)
        onOpenInWindowRequested: actions.openInNewWindow(contextMenu.target.url)
        onOpenAllRequested: actions.openAllIn(contextMenu.target.id)
        onAddPageRequested: actions.addPageTo(root.toolbarId)
        onManageRequested: root.manageBookmarksRequested()
    }
}
