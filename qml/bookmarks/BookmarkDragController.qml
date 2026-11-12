import QtQuick
import Kondor

QtObject {
    id: root

    required property Item preview
    required property BookmarkFolderTree folderTree

    readonly property var emptyRow: ({ title: "", url: "", width: 0, height: 0,
        leftPadding: 0, rightPadding: 0, topPadding: 0, bottomPadding: 0 })

    property var draggedId: -1
    property bool draggedIsFolder: false
    property var draggedRow: root.emptyRow
    property var dropFolderId: -1
    property int dropPosition: -1

    function canDropInto(folderId) {
        return root.folderTree.canMoveInto(root.draggedId, root.draggedIsFolder, folderId)
    }

    function describeRow(row) {
        return { title: row.title.length ? row.title : row.url, url: row.url,
                 width: row.width, height: row.height,
                 leftPadding: row.leftPadding, rightPadding: row.rightPadding,
                 topPadding: row.topPadding, bottomPadding: row.bottomPadding }
    }

    function beginDrag(row, scenePos, pressScenePos) {
        root.draggedId = row.id
        root.draggedIsFolder = row.isFolder
        root.draggedRow = root.describeRow(row)
        root.clearDropTarget()
        root.anchorPreview(row, pressScenePos)
        root.preview.Drag.active = true
        root.moveDragProxy(scenePos)
    }

    function anchorPreview(row, pressScenePos) {
        const origin = row.mapToItem(null, Qt.point(0, 0))
        root.preview.Drag.hotSpot = Qt.point(pressScenePos.x - origin.x, pressScenePos.y - origin.y)
    }

    function moveDragProxy(scenePos) {
        const pos = root.preview.parent.mapFromItem(null, scenePos)
        root.preview.x = pos.x - root.preview.Drag.hotSpot.x
        root.preview.y = pos.y - root.preview.Drag.hotSpot.y
    }

    function finishDrag() {
        if (root.preview.Drag.active)
            root.preview.Drag.drop()
        root.preview.Drag.active = false
        root.endDrag()
    }

    function endDrag() {
        root.draggedId = -1
        root.draggedIsFolder = false
        root.draggedRow = root.emptyRow
        root.clearDropTarget()
    }

    function clearDropTarget() {
        root.dropFolderId = -1
        root.dropPosition = -1
    }
}
