import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor

Menu {
    id: root

    required property BookmarkFolderTree folderTree

    property var targetId: -1
    property var targetParentId: -1
    property bool targetIsFolder: false

    objectName: "itemContextMenu"

    Menu {
        id: moveToMenu
        objectName: "moveToMenu"
        title: qsTr("Move To")
        icon.name: "folder-move"

        Instantiator {
            model: root.folderTree.moveTargets(root.targetId, root.targetParentId, root.targetIsFolder)
            delegate: MenuItem {
                required property var modelData

                text: modelData.title
                leftPadding: Kirigami.Units.largeSpacing * 2 + modelData.depth * 18
                onTriggered: root.folderTree.moveInto(root.targetId, root.targetIsFolder, modelData.id)
            }
            onObjectAdded: function(index, object) { moveToMenu.insertItem(index, object) }
            onObjectRemoved: function(index, object) { moveToMenu.removeItem(object) }
        }
    }
}
