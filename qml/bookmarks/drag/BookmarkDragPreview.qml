import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: root

    required property BookmarkDragController drag

    objectName: "dragProxy"
    width: Math.min(root.drag.draggedRow.width, Kirigami.Units.gridUnit * 20)
    height: root.drag.draggedRow.height
    visible: Drag.active
    z: 1000
    Drag.keys: ["kondor/bookmark"]

    Rectangle {
        anchors.fill: parent
        color: Kirigami.Theme.highlightColor
        opacity: 0.6
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: root.drag.draggedRow.leftPadding
        anchors.rightMargin: root.drag.draggedRow.rightPadding
        anchors.topMargin: root.drag.draggedRow.topPadding
        anchors.bottomMargin: root.drag.draggedRow.bottomPadding
        spacing: Kirigami.Units.largeSpacing

        Kirigami.Icon {
            visible: root.drag.draggedIsFolder
            source: "folder"
            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: 22
            Layout.preferredHeight: 22
        }

        Loader {
            active: root.drag.draggedId >= 0 && !root.drag.draggedIsFolder
            visible: active
            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: 22
            Layout.preferredHeight: 22
            sourceComponent: SiteIcon {
                pageUrl: root.drag.draggedRow.url
            }
        }

        Label {
            objectName: "dragPreviewTitle"
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            text: root.drag.draggedRow.title
            elide: Text.ElideRight
            color: Kirigami.Theme.highlightedTextColor
            font.bold: true
        }
    }
}
