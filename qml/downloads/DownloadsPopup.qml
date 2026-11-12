pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

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

            delegate: DownloadDelegate {}
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
