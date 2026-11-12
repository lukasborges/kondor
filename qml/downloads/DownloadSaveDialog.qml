import QtQuick
import QtQuick.Dialogs
import Kondor

Item {
    id: root

    required property var downloadsPopup

    function askWhereToSave(request, suggestedFile) {
        saveFileDialog.pendingDownload = request
        saveFileDialog.currentFile = suggestedFile
        saveFileDialog.open()
    }

    function acceptPendingDownload() {
        const download = saveFileDialog.pendingDownload
        if (!download)
            return
        applyChosenPath(download, localPath.fromUrl(saveFileDialog.selectedFile))
        download.accept()
        saveFileDialog.pendingDownload = null
    }

    function applyChosenPath(download, path) {
        const slash = path.lastIndexOf("/")
        if (slash <= 0)
            return
        download.downloadDirectory = path.slice(0, slash)
        download.downloadFileName = path.slice(slash + 1)
    }

    function cancelPendingDownload() {
        if (saveFileDialog.pendingDownload)
            saveFileDialog.pendingDownload.cancel()
        saveFileDialog.pendingDownload = null
    }

    LocalPath { id: localPath }

    FileDialog {
        id: saveFileDialog
        title: qsTr("Save File")
        fileMode: FileDialog.SaveFile
        property var pendingDownload: null
        onAccepted: root.acceptPendingDownload()
        onRejected: root.cancelPendingDownload()
    }

    Connections {
        target: DownloadManager
        function onSaveLocationRequested(request, suggestedFile) {
            root.askWhereToSave(request, suggestedFile)
        }
        function onDownloadStarted() { root.downloadsPopup.open() }
    }

    Connections {
        target: DownloadManager.model
        function onCountChanged() {
            if (DownloadManager.model.count === 0)
                root.downloadsPopup.close()
        }
    }
}
