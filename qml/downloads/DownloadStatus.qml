import QtQuick
import Kondor

QtObject {
    id: root

    readonly property var stateHandlers: ({
        [DownloadManager.Requested]: root.requestedText,
        [DownloadManager.InProgress]: root.inProgressText,
        [DownloadManager.Completed]: root.completedText,
        [DownloadManager.Cancelled]: root.canceledText,
        [DownloadManager.Interrupted]: root.failedText
    })

    function text(download) {
        const handler = stateHandlers[download.state]
        return handler ? handler(download) : ""
    }

    function sizeText(bytes) {
        return Qt.locale().formattedDataSize(bytes)
    }

    function requestedText(download) {
        return qsTr("Waiting for confirmation…")
    }

    function inProgressText(download) {
        return download.isPaused ? pausedText(download) : activeText(download)
    }

    function pausedText(download) {
        const received = sizeText(download.receivedBytes)
        if (download.totalBytes <= 0)
            return qsTr("Paused — %1").arg(received)
        return qsTr("Paused — %1 of %2").arg(received).arg(sizeText(download.totalBytes))
    }

    function activeText(download) {
        const received = sizeText(download.receivedBytes)
        if (download.totalBytes <= 0)
            return unknownTotalText(received, download.speedText)
        const done = qsTr("%1 of %2").arg(received).arg(sizeText(download.totalBytes))
        return download.speedText.length > 0 ? qsTr("%1 — %2").arg(done).arg(download.speedText) : done
    }

    function unknownTotalText(received, speedText) {
        if (speedText.length === 0)
            return qsTr("%1 downloaded").arg(received)
        return qsTr("%1 downloaded — %2").arg(received).arg(speedText)
    }

    function completedText(download) {
        return qsTr("Completed — %1").arg(sizeText(download.receivedBytes))
    }

    function canceledText(download) {
        return qsTr("Canceled")
    }

    function failedText(download) {
        if (download.interruptReasonString.length === 0)
            return qsTr("Failed")
        return qsTr("Failed — %1").arg(download.interruptReasonString)
    }
}
