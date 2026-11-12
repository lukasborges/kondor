import QtQuick
import Kondor

QtObject {
    id: root

    property bool done: false
    property bool failed: false
    property bool trashed: false
    property bool trashFailed: false
    property int count: 0
    property string name: ""
    property url file

    function finish(importedCount, fileName) {
        root.count = importedCount
        root.name = fileName
        root.failed = importedCount < 0
        root.trashed = false
        root.trashFailed = false
        root.done = true
    }

    function moveFileToTrash() {
        if (PasswordStore.moveImportFileToTrash(root.file))
            root.trashed = true
        else
            root.trashFailed = true
    }
}
