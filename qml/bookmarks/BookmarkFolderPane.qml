pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: root

    required property var folders
    required property BookmarkSelection selection
    required property BookmarkFolderTree folderTree
    required property BookmarkDragController drag
    required property BookmarkDropTargets dropTargets

    readonly property ListView list: folderList

    function finishDrop(y) {
        root.dropTargets.updateFolderDrop(y)
        const folderId = root.drag.dropFolderId
        root.drag.dropFolderId = -1
        if (folderId > 0)
            root.folderTree.moveInto(root.drag.draggedId, root.drag.draggedIsFolder, folderId)
        root.drag.endDrag()
    }

    SplitView.preferredWidth: 240

    ScrollView {
        anchors.fill: parent
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        background: Rectangle { color: Kirigami.Theme.backgroundColor }

        ListView {
            id: folderList
            objectName: "folderList"
            clip: true
            model: root.folders
            interactive: root.drag.draggedId < 0

            delegate: ItemDelegate {
                id: folderEntry

                required property var modelData
                required property int index

                width: ListView.view.width
                highlighted: folderEntry.modelData.id === root.selection.folderId
                             || folderEntry.modelData.id === root.drag.dropFolderId
                icon.name: "folder"
                text: folderEntry.modelData.title
                leftPadding: 10 + folderEntry.modelData.depth * 18

                Accessible.role: Accessible.ListItem
                Accessible.onPressAction: root.selection.selectFolder(folderEntry.modelData.id)
                onClicked: root.selection.selectFolder(folderEntry.modelData.id)
            }
        }
    }

    DropArea {
        anchors.fill: parent
        keys: ["kondor/bookmark"]

        onEntered: function(drag) { root.dropTargets.updateFolderDrop(drag.y) }
        onPositionChanged: function(drag) { root.dropTargets.updateFolderDrop(drag.y) }
        onExited: root.drag.dropFolderId = -1
        onDropped: function(drop) { root.finishDrop(drop.y) }
    }
}
