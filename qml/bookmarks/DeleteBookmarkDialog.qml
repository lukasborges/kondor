import QtQuick
import Kondor

ConfirmDialog {
    id: root

    required property BookmarkSelection selection

    property var targetId: -1
    property string targetName: ""
    property bool targetIsFolder: true

    objectName: "deleteDialog"
    title: root.targetIsFolder ? qsTr("Delete Folder") : qsTr("Delete Bookmark")
    message: root.targetIsFolder
             ? qsTr("Delete the folder “%1” and everything in it?").arg(root.targetName)
             : qsTr("Delete the bookmark “%1”?").arg(root.targetName)
    acceptText: qsTr("Delete")
    acceptIcon: "edit-delete"
    onAccepted: root.deleteTarget()

    function openFor(target, isFolder) {
        if (!target.id)
            return
        root.targetId = target.id
        root.targetName = target.title
        root.targetIsFolder = isFolder
        root.open()
    }

    function deleteTarget() {
        const info = BookmarkManager.bookmark(root.targetId)
        if (!info.id)
            return
        const fromItemList = root.selection.hasItemSelection() && root.selection.itemId === info.id
        BookmarkManager.remove(info.id)
        root.selectAfterRemoval(info, fromItemList)
    }

    function selectAfterRemoval(info, fromItemList) {
        if (!info.isFolder || fromItemList)
            root.selection.itemId = -1
        else
            root.selection.folderId = info.parentId > 0 ? info.parentId : BookmarkManager.otherFolderId()
    }
}
