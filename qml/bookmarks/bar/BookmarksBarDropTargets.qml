import QtQuick
import Kondor

QtObject {
    id: root

    required property BookmarkDragController drag
    required property BookmarkFolderTree folderTree
    required property Repeater items
    required property int visibleCount

    readonly property bool isRightToLeft: Qt.application.layoutDirection === Qt.RightToLeft

    function itemUnder(x) {
        for (let i = 0; i < root.visibleCount; ++i) {
            const item = root.items.itemAt(i)
            if (item && x >= item.x && x < item.x + item.width)
                return { item: item, ratio: root.leadingRatio(item, x) }
        }
        return root.itemAfterGap(x)
    }

    function itemAfterGap(x) {
        for (let i = 0; i < root.visibleCount; ++i) {
            const item = root.items.itemAt(i)
            if (item && root.isBeforeGap(item, x))
                return { item: item, ratio: 0 }
        }
        return null
    }

    function isBeforeGap(item, x) {
        return root.isRightToLeft ? item.x + item.width <= x : item.x >= x
    }

    function leadingRatio(item, x) {
        const ratio = (x - item.x) / item.width
        return root.isRightToLeft ? 1 - ratio : ratio
    }

    function updateMoveDrop(x) {
        const hit = root.itemUnder(x)
        if (hit && hit.item.id === root.drag.draggedId)
            root.drag.clearDropTarget()
        else if (hit && root.isFolderMiddle(hit))
            root.dropIntoFolder(hit.item.id)
        else
            root.dropAtPosition(hit)
    }

    function isFolderMiddle(hit) {
        return hit.item.isFolder && hit.ratio >= 0.25 && hit.ratio < 0.75
                && root.drag.canDropInto(hit.item.id)
    }

    function dropIntoFolder(id) {
        root.drag.dropFolderId = id
        root.drag.dropPosition = -1
    }

    function dropAtPosition(hit) {
        root.drag.dropFolderId = -1
        root.drag.dropPosition = hit ? hit.item.index + (hit.ratio >= 0.5 ? 1 : 0) : root.visibleCount
    }

    function indicatorX() {
        const position = root.drag.dropPosition
        const edge = position < root.visibleCount ? root.items.itemAt(position) : root.items.itemAt(position - 1)
        if (!edge)
            return root.isRightToLeft ? root.items.parent.width : 0
        const isLeading = position < root.visibleCount
        return edge.x + (isLeading === root.isRightToLeft ? edge.width : 0)
    }

    function completeMove() {
        if (root.drag.dropFolderId > 0)
            root.folderTree.moveInto(root.drag.draggedId, root.drag.draggedIsFolder, root.drag.dropFolderId)
        else if (root.drag.dropPosition >= 0)
            root.drag.moveDraggedTo(BookmarkManager.toolbarModel, BookmarkManager.toolbarFolderId(), root.drag.dropPosition)
        root.drag.clearDropTarget()
    }

    function completeLinkDrop(link) {
        const folderId = BookmarkManager.toolbarFolderId()
        const id = BookmarkManager.addBookmark(link.url, link.title, folderId)
        if (id > 0 && root.drag.dropPosition >= 0)
            BookmarkManager.move(id, folderId, root.drag.dropPosition)
        root.drag.clearDropTarget()
    }
}
