pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// Download list popup, opened from the toolbar button. Every row mirrors a
// live DownloadManager entry: progress, speed, and the actions available for
// its state.
Popup {
    id: root

    width: 440
    padding: 0
    modal: false
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    contentItem: ColumnLayout {
        spacing: 0

        ListView {
            id: listView
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(contentHeight, Kirigami.Units.gridUnit * 24)
            visible: DownloadManager.model.count > 0
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            model: DownloadManager.model

            delegate: ItemDelegate {
                id: delegate
                required property int index
                required property string fileName
                required property string mimeIconName
                required property real progress
                required property int state
                required property bool isPaused
                required property string speedText
                required property string interruptReasonString
                required property real receivedBytes
                required property real totalBytes

                width: listView.width
                padding: Kirigami.Units.largeSpacing

                function sizeText(bytes) {
                    return Qt.locale().formattedDataSize(bytes)
                }

                function statusText() {
                    switch (state) {
                    case DownloadManager.Requested:
                        return qsTr("Waiting for confirmation…")
                    case DownloadManager.InProgress:
                        if (isPaused) {
                            return totalBytes > 0
                                ? qsTr("Paused — %1 of %2").arg(sizeText(receivedBytes)).arg(sizeText(totalBytes))
                                : qsTr("Paused — %1").arg(sizeText(receivedBytes))
                        }
                        if (totalBytes > 0) {
                            const done = qsTr("%1 of %2").arg(sizeText(receivedBytes)).arg(sizeText(totalBytes))
                            return speedText.length > 0 ? qsTr("%1 — %2").arg(done).arg(speedText) : done
                        }
                        return speedText.length > 0
                            ? qsTr("%1 downloaded — %2").arg(sizeText(receivedBytes)).arg(speedText)
                            : qsTr("%1 downloaded").arg(sizeText(receivedBytes))
                    case DownloadManager.Completed:
                        return qsTr("Completed — %1").arg(sizeText(receivedBytes))
                    case DownloadManager.Cancelled:
                        return qsTr("Canceled")
                    case DownloadManager.Interrupted:
                        return interruptReasonString.length > 0
                            ? qsTr("Failed — %1").arg(interruptReasonString)
                            : qsTr("Failed")
                    }
                    return ""
                }

                contentItem: RowLayout {
                    spacing: Kirigami.Units.largeSpacing

                    Kirigami.Icon {
                        source: delegate.mimeIconName
                        Layout.preferredWidth: 32
                        Layout.preferredHeight: 32
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Label {
                            text: delegate.fileName
                            elide: Text.ElideMiddle
                            Layout.fillWidth: true
                        }

                        ProgressBar {
                            Layout.fillWidth: true
                            visible: delegate.state === DownloadManager.InProgress
                            value: delegate.progress >= 0 ? delegate.progress : 0
                            indeterminate: delegate.progress < 0
                        }

                        Label {
                            text: delegate.statusText()
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                            font: Kirigami.Theme.smallFont
                            color: (delegate.state === DownloadManager.Cancelled
                                    || delegate.state === DownloadManager.Interrupted)
                                   ? Kirigami.Theme.negativeTextColor
                                   : Kirigami.Theme.disabledTextColor
                        }
                    }

                    ToolButton {
                        visible: delegate.state === DownloadManager.InProgress
                        display: AbstractButton.IconOnly
                        icon.name: delegate.isPaused ? "media-playback-start" : "media-playback-pause"
                        ToolTip.visible: hovered
                        ToolTip.delay: 600
                        ToolTip.text: delegate.isPaused ? qsTr("Resume") : qsTr("Pause")
                        onClicked: {
                            if (delegate.isPaused)
                                DownloadManager.resume(delegate.index)
                            else
                                DownloadManager.pause(delegate.index)
                        }
                    }

                    ToolButton {
                        visible: delegate.state === DownloadManager.Requested
                                 || delegate.state === DownloadManager.InProgress
                        display: AbstractButton.IconOnly
                        icon.name: "dialog-cancel"
                        ToolTip.visible: hovered
                        ToolTip.delay: 600
                        ToolTip.text: qsTr("Cancel")
                        onClicked: DownloadManager.cancel(delegate.index)
                    }

                    ToolButton {
                        visible: delegate.state === DownloadManager.Completed
                        display: AbstractButton.IconOnly
                        icon.name: "document-open"
                        ToolTip.visible: hovered
                        ToolTip.delay: 600
                        ToolTip.text: qsTr("Open File")
                        onClicked: DownloadManager.openFile(delegate.index)
                    }

                    ToolButton {
                        visible: delegate.state === DownloadManager.Completed
                        display: AbstractButton.IconOnly
                        icon.name: "folder-open"
                        ToolTip.visible: hovered
                        ToolTip.delay: 600
                        ToolTip.text: qsTr("Show in Folder")
                        onClicked: DownloadManager.showInFolder(delegate.index)
                    }

                    ToolButton {
                        visible: delegate.state === DownloadManager.Cancelled
                                 || delegate.state === DownloadManager.Interrupted
                        display: AbstractButton.IconOnly
                        icon.name: "edit-delete"
                        ToolTip.visible: hovered
                        ToolTip.delay: 600
                        ToolTip.text: qsTr("Remove from List")
                        onClicked: DownloadManager.removeFromList(delegate.index)
                    }
                }
            }
        }

        Kirigami.Separator {
            Layout.fillWidth: true
            visible: DownloadManager.model.count > 0
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            visible: DownloadManager.model.count > 0

            Button {
                text: qsTr("Open Downloads Folder")
                icon.name: "folder-download"
                flat: true
                onClicked: DownloadManager.openDownloadsFolder()
            }

            Item { Layout.fillWidth: true }

            Button {
                text: qsTr("Clear Finished")
                icon.name: "edit-clear-history"
                flat: true
                enabled: DownloadManager.hasFinishedDownloads
                onClicked: DownloadManager.clearFinished()
            }
        }
    }
}
