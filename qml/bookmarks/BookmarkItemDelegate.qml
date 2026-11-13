import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ItemDelegate {
    id: root

    required property int index
    required property int id
    required property var parentId
    required property string title
    required property string url
    required property bool isFolder
    required property BookmarkSelection selection
    required property BookmarkDragController drag
    required property BookmarkItemContextMenu contextMenu

    function pickRow() {
        ListView.view.currentIndex = root.index
        ListView.view.forceActiveFocus()
    }

    function showContextMenu() {
        root.selection.itemId = root.id
        root.contextMenu.targetId = root.id
        root.contextMenu.targetParentId = root.parentId
        root.contextMenu.targetIsFolder = root.isFolder
        root.contextMenu.popup()
    }

    function openFolder(button) {
        if (button === Qt.LeftButton)
            root.selection.selectFolder(root.id)
    }

    function activateBookmark(button) {
        root.selection.itemId = root.id
        if (button === Qt.MiddleButton || BookmarkManager.ctrlPressed())
            root.selection.openBookmark(root.url, true)
        else if (Qt.styleHints.singleClickActivation)
            root.selection.openBookmark(root.url, false)
    }

    function pressRow() {
        root.pickRow()
        if (root.isFolder)
            root.openFolder(Qt.LeftButton)
        else
            root.activateBookmark(Qt.LeftButton)
    }

    width: ListView.view.width
    Accessible.role: Accessible.ListItem
    Accessible.onPressAction: root.pressRow()
    highlighted: root.id === root.selection.itemId
                 || root.id === root.drag.dropFolderId
                 || root.id === root.drag.draggedId

    contentItem: RowLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.Icon {
            visible: root.isFolder
            source: "folder"
            Layout.preferredWidth: 22
            Layout.preferredHeight: 22
        }

        SiteIcon {
            visible: !root.isFolder
            pageUrl: root.url
            Layout.preferredWidth: 22
            Layout.preferredHeight: 22
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0

            Label {
                Layout.fillWidth: true
                text: root.title.length ? root.title : root.url
                elide: Text.ElideRight
                font.bold: true
            }

            Label {
                visible: !root.isFolder
                Layout.fillWidth: true
                text: root.url
                elide: Text.ElideRight
                color: root.highlighted ? Kirigami.Theme.highlightedTextColor
                                        : Kirigami.Theme.disabledTextColor
                font: Kirigami.Theme.smallFont
            }
        }
    }

    DragHandler {
        target: null
        grabPermissions: PointerHandler.CanTakeOverFromAnything

        onActiveChanged: {
            if (active)
                root.drag.beginDrag(root, centroid.scenePosition, centroid.scenePressPosition)
            else
                root.drag.finishDrag()
        }
        onCentroidChanged: {
            if (active)
                root.drag.moveDragProxy(centroid.scenePosition)
        }
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton

        onDoubleClicked: function(mouse) {
            if (mouse.button === Qt.LeftButton)
                root.selection.openCurrentItem()
        }
        onClicked: function(mouse) {
            root.pickRow()
            if (mouse.button === Qt.RightButton)
                root.showContextMenu()
            else if (root.isFolder)
                root.openFolder(mouse.button)
            else
                root.activateBookmark(mouse.button)
        }
    }
}
