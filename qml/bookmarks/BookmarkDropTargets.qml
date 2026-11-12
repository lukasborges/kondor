import QtQuick
import Kondor

QtObject {
    id: root

    required property BookmarkDragController drag
    required property ListView folderList
    required property ListView itemList
    required property var folders
    required property var itemModel
    required property string filter
    required property var selectedFolderId

    function rowUnder(list, y) {
        for (let i = 0; i < list.count; ++i) {
            const row = list.itemAtIndex(i)
            const top = row ? row.y - list.contentY : 0
            if (row && y >= top && y < top + row.height)
                return { index: i, ratio: (y - top) / row.height }
        }
        return null
    }

    function updateFolderDrop(y) {
        const hit = root.drag.draggedId > 0 ? root.rowUnder(root.folderList, y) : null
        root.drag.dropFolderId = hit ? root.droppableFolderId(root.folders[hit.index].id) : -1
    }

    function droppableFolderId(folderId) {
        return root.drag.canDropInto(folderId) ? folderId : -1
    }

    function updateItemDrop(y) {
        if (root.drag.draggedId > 0 && root.itemModel)
            root.dropAt(root.rowUnder(root.itemList, y))
        else
            root.drag.clearDropTarget()
    }

    function dropAt(hit) {
        if (!hit) {
            root.dropAfterLastRow()
            return
        }
        const id = root.itemModel.idAt(hit.index)
        if (id <= 0 || id === root.drag.draggedId)
            root.drag.clearDropTarget()
        else
            root.dropOnRow(hit, id)
    }

    function dropAfterLastRow() {
        root.drag.dropFolderId = -1
        root.drag.dropPosition = root.filter.length === 0 ? root.itemList.count : -1
    }

    function dropOnRow(hit, id) {
        if (root.isFolderMiddle(hit, id))
            root.dropIntoFolder(id)
        else if (root.filter.length > 0)
            root.drag.clearDropTarget()
        else
            root.dropBetweenRows(hit)
    }

    function isFolderMiddle(hit, id) {
        return root.itemModel.isFolderAt(hit.index) && hit.ratio >= 0.25 && hit.ratio < 0.75
                && root.drag.canDropInto(id)
    }

    function dropIntoFolder(id) {
        root.drag.dropFolderId = id
        root.drag.dropPosition = -1
    }

    function dropBetweenRows(hit) {
        root.drag.dropFolderId = -1
        root.drag.dropPosition = hit.index + (hit.ratio >= 0.5 ? 1 : 0)
    }

    function dropIndicatorY() {
        if (root.drag.dropPosition < 0)
            return -1
        const count = root.itemList.count
        const above = root.drag.dropPosition < count ? root.itemList.itemAtIndex(root.drag.dropPosition) : null
        if (above)
            return root.clampIndicator(above.y - root.itemList.contentY)
        const last = count > 0 ? root.itemList.itemAtIndex(count - 1) : null
        return last ? root.clampIndicator(last.y + last.height - root.itemList.contentY - 1) : 0
    }

    function clampIndicator(y) {
        return Math.max(0, Math.min(root.itemList.height - 2, y))
    }

    function moveToPosition(id, position) {
        if (position < 0 || !root.itemModel)
            return
        const current = root.itemModel.rowOf(id)
        const target = current >= 0 && current < position ? position - 1 : position
        BookmarkManager.move(id, root.selectedFolderId, target)
    }
}
