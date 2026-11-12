import QtQuick
import Kondor

QtObject {
    id: root

    required property var folders

    signal itemMoved(var id, var folderId)

    function canMoveInto(itemId, isFolder, folderId) {
        if (itemId <= 0 || folderId <= 0 || folderId === itemId)
            return false
        return !isFolder || !root.isInSubtree(folderId, itemId)
    }

    function isInSubtree(folderId, ancestorId) {
        const start = root.folders.findIndex(folder => folder.id === ancestorId)
        if (start < 0)
            return false
        return folderId === ancestorId || root.subtreeAfter(start).some(folder => folder.id === folderId)
    }

    function subtreeAfter(start) {
        const depth = root.folders[start].depth
        const following = root.folders.slice(start + 1)
        const end = following.findIndex(folder => folder.depth <= depth)
        return end < 0 ? following : following.slice(0, end)
    }

    function moveTargets(itemId, parentId, isFolder) {
        return root.folders.filter(folder => folder.id !== parentId
                                   && root.canMoveInto(itemId, isFolder, folder.id))
    }

    function moveInto(id, isFolder, folderId) {
        if (!root.canMoveInto(id, isFolder, folderId))
            return
        BookmarkManager.move(id, folderId, BookmarkManager.childCount(folderId))
        root.itemMoved(id, folderId)
    }
}
