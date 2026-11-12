import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ItemDelegate {
    id: root

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

    readonly property bool isInProgress: state === DownloadManager.InProgress
    readonly property bool isFinishedUnsuccessfully: state === DownloadManager.Cancelled
                                                    || state === DownloadManager.Interrupted

    width: ListView.view.width
    padding: Kirigami.Units.largeSpacing

    function togglePause() {
        if (isPaused)
            DownloadManager.resume(index)
        else
            DownloadManager.pause(index)
    }

    DownloadStatus {
        id: downloadStatus
    }

    contentItem: RowLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.Icon {
            source: root.mimeIconName
            Layout.preferredWidth: 32
            Layout.preferredHeight: 32
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            Label {
                text: root.fileName
                elide: Text.ElideMiddle
                Layout.fillWidth: true
            }

            ProgressBar {
                Layout.fillWidth: true
                visible: root.isInProgress
                value: root.progress >= 0 ? root.progress : 0
                indeterminate: root.progress < 0
            }

            Label {
                text: downloadStatus.text(root)
                elide: Text.ElideRight
                Layout.fillWidth: true
                font: Kirigami.Theme.smallFont
                color: root.isFinishedUnsuccessfully
                       ? Kirigami.Theme.negativeTextColor
                       : Kirigami.Theme.disabledTextColor
            }
        }

        ToolButton {
            visible: root.isInProgress
            display: AbstractButton.IconOnly
            icon.name: root.isPaused ? "media-playback-start" : "media-playback-pause"
            ToolTip.visible: hovered
            ToolTip.delay: 600
            ToolTip.text: root.isPaused ? qsTr("Resume") : qsTr("Pause")
            onClicked: root.togglePause()
        }

        ToolButton {
            visible: root.state === DownloadManager.Requested || root.isInProgress
            display: AbstractButton.IconOnly
            icon.name: "dialog-cancel"
            ToolTip.visible: hovered
            ToolTip.delay: 600
            ToolTip.text: qsTr("Cancel")
            onClicked: DownloadManager.cancel(root.index)
        }

        ToolButton {
            visible: root.state === DownloadManager.Completed
            display: AbstractButton.IconOnly
            icon.name: "document-open"
            ToolTip.visible: hovered
            ToolTip.delay: 600
            ToolTip.text: qsTr("Open File")
            onClicked: DownloadManager.openFile(root.index)
        }

        ToolButton {
            visible: root.state === DownloadManager.Completed
            display: AbstractButton.IconOnly
            icon.name: "folder-open"
            ToolTip.visible: hovered
            ToolTip.delay: 600
            ToolTip.text: qsTr("Show in Folder")
            onClicked: DownloadManager.showInFolder(root.index)
        }

        ToolButton {
            visible: root.isFinishedUnsuccessfully
            display: AbstractButton.IconOnly
            icon.name: "edit-delete"
            ToolTip.visible: hovered
            ToolTip.delay: 600
            ToolTip.text: qsTr("Remove from List")
            onClicked: DownloadManager.removeFromList(root.index)
        }
    }
}
