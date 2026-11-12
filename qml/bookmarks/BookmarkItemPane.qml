import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: root

    required property var itemModel
    required property BookmarkSelection selection
    required property BookmarkFolderTree folderTree
    required property BookmarkDragController drag
    required property BookmarkDropTargets dropTargets
    required property BookmarkItemContextMenu contextMenu

    readonly property ListView list: itemList

    function setCurrentRow(row) {
        itemList.currentIndex = row
    }

    function mirrorCurrentRow() {
        if (itemList.activeFocus && root.itemModel && itemList.currentIndex >= 0)
            root.selection.itemId = root.itemModel.idAt(itemList.currentIndex)
    }

    function finishDrop(y) {
        root.dropTargets.updateItemDrop(y)
        if (root.drag.dropFolderId > 0)
            root.folderTree.moveInto(root.drag.draggedId, root.drag.draggedIsFolder, root.drag.dropFolderId)
        else if (root.drag.dropPosition >= 0)
            root.dropTargets.moveToPosition(root.drag.draggedId, root.drag.dropPosition)
        root.drag.endDrag()
    }

    SplitView.fillWidth: true

    ScrollView {
        id: itemScroll
        anchors.fill: parent
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        background: Rectangle { color: Kirigami.Theme.backgroundColor }

        ListView {
            id: itemList
            objectName: "itemList"
            clip: true
            model: root.itemModel
            focus: true
            interactive: root.drag.draggedId < 0

            Keys.onReturnPressed: root.selection.openCurrentItem()
            Keys.onEnterPressed: root.selection.openCurrentItem()
            onCurrentIndexChanged: root.mirrorCurrentRow()

            delegate: BookmarkItemDelegate {
                selection: root.selection
                drag: root.drag
                contextMenu: root.contextMenu
            }
        }
    }

    DropArea {
        anchors.fill: itemScroll
        keys: ["kondor/bookmark"]

        onEntered: function(drag) { root.dropTargets.updateItemDrop(drag.y) }
        onPositionChanged: function(drag) { root.dropTargets.updateItemDrop(drag.y) }
        onExited: root.drag.clearDropTarget()
        onDropped: function(drop) { root.finishDrop(drop.y) }
    }

    Rectangle {
        visible: root.drag.dropPosition >= 0
        width: itemScroll.width
        height: 2
        color: Kirigami.Theme.highlightColor
        y: root.dropTargets.dropIndicatorY()
        z: 2
    }
}
