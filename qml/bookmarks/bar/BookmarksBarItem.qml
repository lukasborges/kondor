import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ToolButton {
    id: root

    required property int index
    required property int id
    required property string title
    required property string url
    required property bool isFolder
    required property BookmarkDragController drag

    signal backgroundOpenRequested()
    signal contextMenuRequested()

    function isContextMenuKey(event) {
        return event.key === Qt.Key_F10 && (event.modifiers & Qt.ShiftModifier)
    }

    flat: true
    padding: Kirigami.Units.smallSpacing
    highlighted: root.id === root.drag.dropFolderId || root.id === root.drag.draggedId
    Accessible.name: root.title
    Accessible.description: root.isFolder ? qsTr("folder") : ""
    ToolTip.visible: hovered && root.drag.draggedId < 0
    ToolTip.text: root.isFolder ? root.title : root.url
    ToolTip.delay: 600
    Keys.onMenuPressed: root.contextMenuRequested()
    Keys.onEscapePressed: root.drag.cancelDrag()
    Keys.onPressed: function(event) {
        if (root.isContextMenuKey(event))
            root.contextMenuRequested()
        event.accepted = root.isContextMenuKey(event)
    }

    contentItem: RowLayout {
        spacing: Kirigami.Units.smallSpacing

        Kirigami.Icon {
            visible: root.isFolder
            source: "folder"
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
        }

        SiteIcon {
            visible: !root.isFolder
            pageUrl: root.url
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
        }

        Label {
            Layout.maximumWidth: Kirigami.Units.gridUnit * 14
            text: root.title.length ? root.title : root.url
            elide: Text.ElideRight
        }

        Kirigami.Icon {
            visible: root.isFolder
            source: "arrow-down"
            Layout.preferredWidth: 10
            Layout.preferredHeight: 10
        }
    }

    TapHandler {
        acceptedButtons: Qt.MiddleButton
        onTapped: if (!root.isFolder) root.backgroundOpenRequested()
    }

    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: root.contextMenuRequested()
    }

    DragHandler {
        target: null
        acceptedButtons: Qt.LeftButton
        grabPermissions: PointerHandler.CanTakeOverFromAnything

        onActiveChanged: {
            if (active)
                root.beginDrag(centroid)
            else
                root.drag.finishDrag()
        }
        onCentroidChanged: {
            if (active)
                root.drag.moveDragProxy(centroid.scenePosition)
        }
    }

    function beginDrag(centroid) {
        root.forceActiveFocus()
        root.drag.beginDrag(root, centroid.scenePosition, centroid.scenePressPosition)
    }
}
