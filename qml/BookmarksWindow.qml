pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// "Manage Bookmarks" window (Ctrl+Shift+O): folder tree on the left, the items
// of the selected folder on the right. Created on demand in BrowserWindow.qml. Visuals
// follow the 02b-bookmarks-manager.qml prototype.
ApplicationWindow {
    id: root
    width: 820
    height: 540
    title: qsTr("Manage Bookmarks")
    visible: false

    required property TabModel tabModel

    property var selectedFolderId: BookmarkManager.otherFolderId()
    // Row picked in the right-hand list (0 means "none"); the toolbar actions
    // then apply to that item instead of the selected folder. Tracked
    // explicitly because a ListView sets currentIndex to 0 as soon as its
    // model has items, which must not count as a user selection.
    property var selectedItemId: -1
    property string filter: ""

    // Drag and drop state: the item being dragged out of the right-hand list
    // (-1 when idle), the folder row highlighted as a drop target and the
    // insertion row shown as a line (0..count, -1 when none).
    property var draggedId: -1
    property bool draggedIsFolder: false
    // Appearance of the drag preview, captured from the source row when the
    // gesture starts so the preview can be built outside the list.
    property string draggedTitle: ""
    property string draggedUrl: ""
    property real draggedWidth: 0
    property real draggedHeight: 0
    property real draggedPaddingLeft: 0
    property real draggedPaddingRight: 0
    property real draggedPaddingTop: 0
    property real draggedPaddingBottom: 0
    property var dropFolderId: -1
    property int dropPosition: -1
    // Model that currently carries `filter`, so it can be cleared on switch.
    property var filteredModel: null

    onSelectedFolderIdChanged: root.selectedItemId = -1

    // Rebuilt whenever a bookmark write bumps the revision.
    property var folders: {
        const revision = BookmarkManager.revision
        return revision >= 0 ? BookmarkManager.folders : []
    }

    property var itemModel: {
        const revision = BookmarkManager.revision
        return revision >= 0 ? BookmarkManager.modelForFolder(root.selectedFolderId) : null
    }

    // The current model keeps the search term; the previous one is cleared so
    // a stale filter can never make another folder (the bookmarks toolbar
    // shares its model) show the wrong rows.
    onItemModelChanged: {
        if (root.filteredModel && root.filteredModel !== root.itemModel)
            root.filteredModel.filter = ""
        root.filteredModel = root.itemModel
        if (root.itemModel)
            root.itemModel.filter = root.filter
    }

    onFilterChanged: {
        if (root.itemModel)
            root.itemModel.filter = root.filter
    }

    onClosing: function(close) {
        // Do not destroy: just hide, so it reopens quickly.
        close.accepted = false
        root.visible = false
    }

    function showWindow() {
        root.visible = true
        root.raise()
        root.requestActivate()
    }

    function selectedInfo() {
        const revision = BookmarkManager.revision
        return revision >= 0 ? BookmarkManager.bookmark(root.selectedFolderId) : {}
    }

    function openBookmark(url, background) {
        if (!url)
            return
        const tab = root.tabModel.currentTab
        if (!tab) {
            root.tabModel.addTab(false, url)
        } else if (background) {
            // A new tab keeps the current mode: private stays private.
            const profile = tab.isPrivate ? ProfileManager.createPrivateProfile()
                                          : ProfileManager.defaultProfile()
            root.tabModel.addTabWithProfile(profile, url, true)
        } else {
            tab.navigateTo(url)
        }
    }

    // True when the user picked a row in the right-hand list: the toolbar
    // actions then apply to that bookmark/folder instead of the folder
    // selected in the tree. Reads the revision so the actions are
    // re-evaluated after writes (for example when the picked item is gone).
    function hasItemSelection() {
        const revision = BookmarkManager.revision
        if (revision < 0 || !(root.selectedItemId > 0))
            return false
        return BookmarkManager.bookmark(root.selectedItemId).id > 0
    }

    function currentItemInfo() {
        if (!root.hasItemSelection())
            return {}
        return BookmarkManager.bookmark(root.selectedItemId)
    }

    // The item the toolbar actions apply to: the row of the right-hand list
    // when there is one, the selected folder otherwise.
    function actionTarget() {
        return root.hasItemSelection() ? root.currentItemInfo() : root.selectedInfo()
    }

    function actionIsFolder() {
        return root.hasItemSelection() ? root.currentItemInfo().isFolder : true
    }

    // ── Drag and drop and "Move To" helpers ────────────────────────────

    // A folder can never be dropped into itself or one of its descendants.
    function canMoveInto(itemId, isFolder, folderId) {
        if (itemId <= 0 || folderId <= 0)
            return false
        if (folderId === itemId)
            return false
        return !isFolder || !root.isInSubtree(folderId, itemId)
    }

    function canDropInto(folderId) {
        return root.canMoveInto(root.draggedId, root.draggedIsFolder, folderId)
    }

    // The folders property is a depth-first flat list, so a subtree is every
    // following row with a greater depth.
    function isInSubtree(folderId, ancestorId) {
        const folders = root.folders
        let ancestorDepth = -1
        for (let i = 0; i < folders.length; ++i) {
            const folder = folders[i]
            if (ancestorDepth < 0) {
                if (folder.id !== ancestorId)
                    continue
                if (folder.id === folderId)
                    return true
                ancestorDepth = folder.depth
                continue
            }
            if (folder.depth <= ancestorDepth)
                return false
            if (folder.id === folderId)
                return true
        }
        return false
    }

    // pressScenePos is where the pointer went down; scenePos has already
    // passed the drag threshold, so the hot spot uses the press position to
    // keep the preview exactly where the row was grabbed.
    function beginDrag(row, scenePos, pressScenePos) {
        root.draggedId = row.id
        root.draggedIsFolder = row.isFolder
        root.draggedTitle = row.title.length ? row.title : row.url
        root.draggedUrl = row.url
        root.draggedWidth = row.width
        root.draggedHeight = row.height
        root.draggedPaddingLeft = row.leftPadding
        root.draggedPaddingRight = row.rightPadding
        root.draggedPaddingTop = row.topPadding
        root.draggedPaddingBottom = row.bottomPadding
        root.clearDropTarget()
        // The drag source is a single proxy item: a row inside a view cannot
        // follow the pointer, so the window-level proxy carries the drag.
        // Keep the offset between the pointer and the row it grabbed, so the
        // preview stays where the row was pressed (like Firefox's Library).
        const rowOrigin = row.mapToItem(null, Qt.point(0, 0))
        dragProxy.Drag.hotSpot = Qt.point(pressScenePos.x - rowOrigin.x,
                                         pressScenePos.y - rowOrigin.y)
        dragProxy.Drag.active = true
        root.moveDragProxy(scenePos)
    }

    // Keeps the proxy's hot spot under the pointer, so every DropArea sees
    // real drag positions (the left tree included).
    function moveDragProxy(scenePos) {
        const pos = dragProxy.parent.mapFromItem(null, scenePos)
        dragProxy.x = pos.x - dragProxy.Drag.hotSpot.x
        dragProxy.y = pos.y - dragProxy.Drag.hotSpot.y
    }

    // Ends the gesture with a real drop at the last position. Turning
    // Drag.active off without Drag.drop() cancels the drag instead.
    function finishDrag() {
        if (dragProxy.Drag.active)
            dragProxy.Drag.drop()
        dragProxy.Drag.active = false
        root.endDrag()
    }

    function endDrag() {
        root.draggedId = -1
        root.draggedIsFolder = false
        root.draggedTitle = ""
        root.draggedUrl = ""
        root.draggedWidth = 0
        root.draggedHeight = 0
        root.clearDropTarget()
    }

    function clearDropTarget() {
        root.dropFolderId = -1
        root.dropPosition = -1
    }

    // Moves to the end of `folderId`. The selected folder stays selected; a
    // moved item that left the current list is no longer the action target.
    function moveInto(id, isFolder, folderId) {
        if (!root.canMoveInto(id, isFolder, folderId))
            return
        BookmarkManager.move(id, folderId, BookmarkManager.childCount(folderId))
        if (root.selectedItemId === id && folderId !== root.selectedFolderId)
            root.selectedItemId = -1
    }

    // `position` is the gap between visible rows (0..count) in the current
    // folder. Moving down shifts by one because the dragged row is removed
    // before it is inserted again.
    function moveToPosition(id, position) {
        if (position < 0 || !root.itemModel)
            return
        const current = root.itemModel.rowOf(id)
        const target = current >= 0 && current < position ? position - 1 : position
        BookmarkManager.move(id, root.selectedFolderId, target)
    }

    // Decides which folder of the left tree is under `y` (the tree pane's
    // drag position). A single DropArea over the whole tree is used instead of
    // one per delegate: a delegate DropArea depends on the view's own drag
    // delivery, which does not fire reliably with real input once the pointer
    // leaves the right-hand list.
    function updateFolderDrop(y) {
        if (root.draggedId <= 0) {
            root.dropFolderId = -1
            return
        }
        const count = folderList.count
        for (let i = 0; i < count; ++i) {
            const row = folderList.itemAtIndex(i)
            if (!row)
                continue
            const top = row.y - folderList.contentY
            if (y >= top && y < top + row.height) {
                const folderId = root.folders[i].id
                root.dropFolderId = root.canDropInto(folderId) ? folderId : -1
                return
            }
        }
        root.dropFolderId = -1
    }

    // Decides what is under the pointer in the right-hand list: a folder to
    // move into (its middle band) or a gap to insert into (the top and bottom
    // bands of every row, by half).
    function updateItemDrop(y) {
        if (root.draggedId <= 0 || !root.itemModel) {
            root.clearDropTarget()
            return
        }
        const count = itemList.count
        let hovered = -1
        let ratio = 0
        for (let i = 0; i < count; ++i) {
            const row = itemList.itemAtIndex(i)
            if (!row)
                continue
            const top = row.y - itemList.contentY
            if (y >= top && y < top + row.height) {
                hovered = i
                ratio = (y - top) / row.height
                break
            }
        }
        if (hovered < 0) {
            // Empty space below the last row: append to the current folder.
            root.dropFolderId = -1
            root.dropPosition = root.filter.length === 0 ? count : -1
            return
        }
        const id = root.itemModel.idAt(hovered)
        if (id <= 0 || id === root.draggedId) {
            root.clearDropTarget()
            return
        }
        if (root.itemModel.isFolderAt(hovered) && ratio >= 0.25 && ratio < 0.75
                && root.canDropInto(id)) {
            root.dropFolderId = id
            root.dropPosition = -1
            return
        }
        // Reordering by visible rows only makes sense without a search filter.
        if (root.filter.length > 0) {
            root.clearDropTarget()
            return
        }
        root.dropFolderId = -1
        root.dropPosition = hovered + (ratio >= 0.5 ? 1 : 0)
    }

    function dropIndicatorY() {
        if (root.dropPosition < 0)
            return -1
        if (root.dropPosition < itemList.count) {
            const row = itemList.itemAtIndex(root.dropPosition)
            if (row)
                return Math.max(0, Math.min(itemList.height - 2, row.y - itemList.contentY))
        }
        const count = itemList.count
        if (count > 0) {
            const last = itemList.itemAtIndex(count - 1)
            if (last) {
                return Math.max(0, Math.min(itemList.height - 2,
                                               last.y + last.height - itemList.contentY - 1))
            }
        }
        return 0
    }

    // Folders offered by "Move To": everything except the item's own folder
    // and, for a folder, its subtree.
    function moveToTargets(itemId, parentId, isFolder) {
        const folders = root.folders
        const targets = []
        for (let i = 0; i < folders.length; ++i) {
            const folder = folders[i]
            if (folder.id === parentId)
                continue
            if (!root.canMoveInto(itemId, isFolder, folder.id))
                continue
            targets.push(folder)
        }
        return targets
    }

    function moveSelected(delta) {
        // Up/Down follow the visible rows, which only match the stored order
        // while no search filter is applied.
        if (root.filter.length > 0)
            return
        const info = root.actionTarget()
        if (!info.id || info.special)
            return
        const parentId = root.hasItemSelection() ? root.selectedFolderId : info.parentId
        const movedId = info.id
        BookmarkManager.move(movedId, parentId, info.position + delta)
        if (!root.hasItemSelection())
            return
        // Keep the moved bookmark as the current row after the model reset.
        const row = root.itemModel ? root.itemModel.rowOf(movedId) : -1
        if (row >= 0)
            itemList.currentIndex = row
    }

    function openCurrentItem() {
        const info = root.currentItemInfo()
        if (!info.id)
            return
        if (info.isFolder)
            root.selectedFolderId = info.id
        else
            root.openBookmark(info.url)
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        ToolBar {
            Layout.fillWidth: true

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 4
                anchors.rightMargin: 4
                spacing: 4

                ToolButton {
                    text: qsTr("New Folder")
                    icon.name: "folder-new"
                    onClicked: newFolderDialog.open()
                }
                ToolButton {
                    text: qsTr("Rename")
                    icon.name: "edit-rename"
                    enabled: root.hasItemSelection() || root.selectedFolderId > 0
                    onClicked: {
                        const target = root.actionTarget()
                        if (!target.id)
                            return
                        renameDialog.targetId = target.id
                        renameDialog.targetIsFolder = root.actionIsFolder()
                        renameDialog.targetTitle = target.title
                        renameDialog.open()
                    }
                }
                ToolButton {
                    text: qsTr("Delete")
                    icon.name: "edit-delete"
                    enabled: root.hasItemSelection()
                             || (root.selectedFolderId > 0 && !root.selectedInfo().special)
                    onClicked: {
                        const target = root.actionTarget()
                        if (!target.id)
                            return
                        deleteDialog.targetId = target.id
                        deleteDialog.targetIsFolder = root.actionIsFolder()
                        deleteDialog.open()
                    }
                }
                ToolButton {
                    display: AbstractButton.IconOnly
                    icon.name: "go-up"
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Move Up")
                    ToolTip.delay: 600
                    enabled: root.filter.length === 0
                             && (root.hasItemSelection() || !root.selectedInfo().special)
                             && root.actionTarget().id > 0
                    onClicked: root.moveSelected(-1)
                }
                ToolButton {
                    display: AbstractButton.IconOnly
                    icon.name: "go-down"
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Move Down")
                    ToolTip.delay: 600
                    enabled: root.filter.length === 0
                             && (root.hasItemSelection() || !root.selectedInfo().special)
                             && root.actionTarget().id > 0
                    onClicked: root.moveSelected(1)
                }

                Item { Layout.fillWidth: true }

                ToolButton {
                    text: qsTr("Import from HTML…")
                    icon.name: "document-import"
                    onClicked: importDialog.open()
                }

                TextField {
                    id: searchField
                    Layout.preferredWidth: Kirigami.Units.gridUnit * 14
                    placeholderText: qsTr("Search bookmarks…")
                    onTextChanged: searchTimer.restart()
                }
            }
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Item {
                SplitView.preferredWidth: 240

                ScrollView {
                    id: folderScroll
                    anchors.fill: parent
                    Kirigami.Theme.colorSet: Kirigami.Theme.View
                    Kirigami.Theme.inherit: false
                    background: Rectangle { color: Kirigami.Theme.backgroundColor }

                    ListView {
                        id: folderList
                        clip: true
                        model: root.folders
                        // A flick must never take the pointer grab from the
                        // drag that is crossing the panes.
                        interactive: root.draggedId < 0

                        delegate: ItemDelegate {
                            id: folderEntry

                            required property var modelData
                            required property int index

                            width: ListView.view.width
                            highlighted: folderEntry.modelData.id === root.selectedFolderId
                                         || folderEntry.modelData.id === root.dropFolderId
                            icon.name: "folder"
                            text: folderEntry.modelData.title
                            leftPadding: 10 + folderEntry.modelData.depth * 18

                            onClicked: {
                                // Clear even when the same folder is clicked again,
                                // so the actions always go back to the folder.
                                root.selectedItemId = -1
                                root.selectedFolderId = folderEntry.modelData.id
                            }
                        }
                    }
                }

                // Drag target for the whole tree, so the drag position is
                // always handled at pane level (the same way as the list on the
                // right) instead of inside a recycled delegate.
                DropArea {
                    id: treeDrop
                    anchors.fill: parent
                    keys: ["kondor/bookmark"]

                    onEntered: function(drag) {
                        root.updateFolderDrop(drag.y)
                    }
                    onPositionChanged: function(drag) {
                        root.updateFolderDrop(drag.y)
                    }
                    onExited: root.dropFolderId = -1
                    onDropped: function(drop) {
                        root.updateFolderDrop(drop.y)
                        const folderId = root.dropFolderId
                        root.dropFolderId = -1
                        if (folderId > 0)
                            root.moveInto(root.draggedId, root.draggedIsFolder, folderId)
                        root.endDrag()
                    }
                }
            }

            Item {
                SplitView.fillWidth: true

                ScrollView {
                    id: itemScroll
                    anchors.fill: parent
                    Kirigami.Theme.colorSet: Kirigami.Theme.View
                    Kirigami.Theme.inherit: false
                    background: Rectangle { color: Kirigami.Theme.backgroundColor }

                    ListView {
                        id: itemList
                        clip: true
                        model: root.itemModel
                        focus: true
                        // Do not let a flick steal the grab from the row drag.
                        interactive: root.draggedId < 0

                        Keys.onReturnPressed: root.openCurrentItem()
                        Keys.onEnterPressed: root.openCurrentItem()

                        // Arrow keys move currentIndex; mirror that into the
                        // explicit selection so the highlight and the actions
                        // target the same row.
                        onCurrentIndexChanged: {
                            if (itemList.activeFocus && root.itemModel && itemList.currentIndex >= 0)
                                root.selectedItemId = root.itemModel.idAt(itemList.currentIndex)
                        }

                        delegate: ItemDelegate {
                            id: itemEntry

                            required property int index
                            required property int id
                            required property var parentId
                            required property string title
                            required property string url
                            required property bool isFolder

                            width: ListView.view.width
                            // The row being dragged stays highlighted while
                            // the preview follows the pointer.
                            highlighted: itemEntry.id === root.selectedItemId
                                         || itemEntry.id === root.dropFolderId
                                         || itemEntry.id === root.draggedId

                            contentItem: RowLayout {
                                spacing: Kirigami.Units.largeSpacing

                                Kirigami.Icon {
                                    visible: itemEntry.isFolder
                                    source: "folder"
                                    Layout.preferredWidth: 22
                                    Layout.preferredHeight: 22
                                }

                                SiteIcon {
                                    visible: !itemEntry.isFolder
                                    pageUrl: itemEntry.url
                                    Layout.preferredWidth: 22
                                    Layout.preferredHeight: 22
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 0

                                    Label {
                                        Layout.fillWidth: true
                                        text: itemEntry.title.length ? itemEntry.title : itemEntry.url
                                        elide: Text.ElideRight
                                        font.bold: true
                                    }

                                    Label {
                                        visible: !itemEntry.isFolder
                                        Layout.fillWidth: true
                                        text: itemEntry.url
                                        elide: Text.ElideRight
                                        color: itemEntry.highlighted
                                               ? Kirigami.Theme.highlightedTextColor
                                               : Kirigami.Theme.disabledTextColor
                                        font: Kirigami.Theme.smallFont
                                    }
                                }
                            }

                            DragHandler {
                                id: dragHandler
                                // Only track the gesture: the window-level
                                // proxy follows the pointer, the row stays.
                                target: null
                                // Keep the grab until the button is released:
                                // the right list's Flickable (and the tree's)
                                // must not cancel the drag while the pointer
                                // crosses into the other pane.
                                grabPermissions: PointerHandler.CanTakeOverFromAnything

                                onActiveChanged: {
                                    if (active) {
                                        root.beginDrag(itemEntry, centroid.scenePosition,
                                                       centroid.scenePressPosition)
                                    } else {
                                        root.finishDrag()
                                    }
                                }
                                onCentroidChanged: {
                                    if (active)
                                        root.moveDragProxy(centroid.scenePosition)
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton

                                onDoubleClicked: function(mouse) {
                                    if (mouse.button === Qt.LeftButton)
                                        root.openCurrentItem()
                                }
                                onClicked: function(mouse) {
                                    itemList.currentIndex = itemEntry.index
                                    itemList.forceActiveFocus()
                                    if (mouse.button === Qt.RightButton) {
                                        root.selectedItemId = itemEntry.id
                                        itemContextMenu.targetId = itemEntry.id
                                        itemContextMenu.targetParentId = itemEntry.parentId
                                        itemContextMenu.targetIsFolder = itemEntry.isFolder
                                        itemContextMenu.popup()
                                        return
                                    }
                                    if (itemEntry.isFolder) {
                                        if (mouse.button === Qt.LeftButton) {
                                            root.selectedItemId = -1
                                            root.selectedFolderId = itemEntry.id
                                        }
                                        return
                                    }
                                    root.selectedItemId = itemEntry.id
                                    if (mouse.button === Qt.MiddleButton) {
                                        root.openBookmark(itemEntry.url, true)
                                        return
                                    }
                                    if (BookmarkManager.ctrlPressed()) {
                                        root.openBookmark(itemEntry.url, true)
                                        return
                                    }
                                    // Qt.styleHints is typed QObject* in the QML
                                    // global object, but returns a QStyleHints at
                                    // runtime.
                                    // qmllint disable missing-property
                                    if (Qt.styleHints.singleClickActivation)
                                        root.openBookmark(itemEntry.url, false)
                                }
                            }
                        }
                    }
                }

                DropArea {
                    id: itemDrop
                    anchors.fill: itemScroll
                    keys: ["kondor/bookmark"]

                    onEntered: function(drag) {
                        root.updateItemDrop(drag.y)
                    }
                    onPositionChanged: function(drag) {
                        root.updateItemDrop(drag.y)
                    }
                    onExited: root.clearDropTarget()
                    onDropped: function(drop) {
                        root.updateItemDrop(drop.y)
                        if (root.dropFolderId > 0)
                            root.moveInto(root.draggedId, root.draggedIsFolder, root.dropFolderId)
                        else if (root.dropPosition >= 0)
                            root.moveToPosition(root.draggedId, root.dropPosition)
                        root.endDrag()
                    }
                }

                Rectangle {
                    id: dropIndicator
                    visible: root.dropPosition >= 0
                    width: itemScroll.width
                    height: 2
                    color: Kirigami.Theme.highlightColor
                    y: root.dropIndicatorY()
                    z: 2
                }
            }
        }
    }

    Timer {
        id: searchTimer
        interval: 200
        onTriggered: root.filter = searchField.text
    }

    // Drag source and preview that follows the pointer while a row's
    // DragHandler is active. Keeping it at window level (instead of the row
    // itself) makes the drag reach every DropArea, including the folder tree,
    // and keeps the preview above both panes (not clipped by a ScrollView).
    // It has no input handlers, so it never takes input.
    Item {
        id: dragProxy
        width: Math.min(root.draggedWidth, Kirigami.Units.gridUnit * 20)
        height: root.draggedHeight
        visible: dragProxy.Drag.active
        z: 1000
        Drag.keys: ["kondor/bookmark"]

        Rectangle {
            anchors.fill: parent
            color: Kirigami.Theme.highlightColor
            opacity: 0.6
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: root.draggedPaddingLeft
            anchors.rightMargin: root.draggedPaddingRight
            anchors.topMargin: root.draggedPaddingTop
            anchors.bottomMargin: root.draggedPaddingBottom
            spacing: Kirigami.Units.largeSpacing

            Kirigami.Icon {
                visible: root.draggedIsFolder
                source: "folder"
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: 22
                Layout.preferredHeight: 22
            }

            // A Loader keeps the favicon request from happening at window
            // creation, when no row is being dragged yet.
            Loader {
                active: root.draggedId >= 0 && !root.draggedIsFolder
                visible: active
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: 22
                Layout.preferredHeight: 22
                sourceComponent: SiteIcon {
                    pageUrl: root.draggedUrl
                }
            }

            Label {
                objectName: "dragPreviewTitle"
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                text: root.draggedTitle
                elide: Text.ElideRight
                color: Kirigami.Theme.highlightedTextColor
                font.bold: true
            }
        }
    }

    // Right-click menu of the right-hand list: "Move To" is a submenu with
    // every valid folder, indented like the tree.
    Menu {
        id: itemContextMenu

        property var targetId: -1
        property var targetParentId: -1
        property bool targetIsFolder: false

        Menu {
            id: moveToMenu
            title: qsTr("Move To")
            icon.name: "folder-move"

            Instantiator {
                model: root.moveToTargets(itemContextMenu.targetId,
                                          itemContextMenu.targetParentId,
                                          itemContextMenu.targetIsFolder)
                delegate: MenuItem {
                    required property var modelData

                    text: modelData.title
                    leftPadding: Kirigami.Units.largeSpacing * 2 + modelData.depth * 18
                    onTriggered: root.moveInto(itemContextMenu.targetId,
                                               itemContextMenu.targetIsFolder,
                                               modelData.id)
                }
                onObjectAdded: function(index, object) {
                    moveToMenu.insertItem(index, object)
                }
                onObjectRemoved: function(index, object) {
                    moveToMenu.removeItem(object)
                }
            }
        }
    }

    Dialog {
        id: newFolderDialog
        title: qsTr("New Folder")
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        anchors.centerIn: parent

        onOpened: newFolderField.forceActiveFocus()

        ColumnLayout {
            spacing: Kirigami.Units.smallSpacing

            Label {
                text: qsTr("Name:")
            }

            TextField {
                id: newFolderField
                //: Default name of a new bookmark folder
                placeholderText: qsTr("New Folder")
                Layout.fillWidth: true
                Layout.preferredWidth: Kirigami.Units.gridUnit * 18
                onAccepted: newFolderDialog.accept()
            }
        }

        onAccepted: {
            const id = BookmarkManager.addFolder(newFolderField.text, root.selectedFolderId)
            if (id > 0)
                root.selectedFolderId = id
            newFolderField.text = ""
        }
        onRejected: newFolderField.text = ""
    }

    Dialog {
        id: renameDialog
        property var targetId: -1
        property bool targetIsFolder: true
        property string targetTitle: ""
        title: renameDialog.targetIsFolder ? qsTr("Rename Folder") : qsTr("Rename Bookmark")
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        anchors.centerIn: parent

        onOpened: {
            renameField.text = renameDialog.targetTitle
            renameField.selectAll()
            renameField.forceActiveFocus()
        }

        ColumnLayout {
            spacing: Kirigami.Units.smallSpacing

            Label {
                text: qsTr("New name:")
            }

            TextField {
                id: renameField
                Layout.fillWidth: true
                Layout.preferredWidth: Kirigami.Units.gridUnit * 18
                onAccepted: {
                    if (renameField.text.trim().length > 0)
                        renameDialog.accept()
                }
            }
        }

        Component.onCompleted: standardButton(Dialog.Ok).enabled = Qt.binding(function() {
            return renameField.text.trim().length > 0
        })

        onAccepted: {
            if (renameDialog.targetId > 0)
                BookmarkManager.rename(renameDialog.targetId, renameField.text)
        }
    }

    MessageDialog {
        id: deleteDialog
        property var targetId: -1
        property bool targetIsFolder: true
        title: deleteDialog.targetIsFolder ? qsTr("Delete Folder") : qsTr("Delete Bookmark")
        text: deleteDialog.targetIsFolder
              ? qsTr("Delete this folder and everything in it?")
              : qsTr("Delete this bookmark?")
        buttons: MessageDialog.Yes | MessageDialog.No
        onAccepted: {
            const info = BookmarkManager.bookmark(deleteDialog.targetId)
            if (!info.id)
                return
            const fromItemList = root.hasItemSelection() && root.selectedItemId === info.id
            BookmarkManager.remove(info.id)
            if (!info.isFolder || fromItemList) {
                // The picked row is gone; actions go back to the tree folder.
                root.selectedItemId = -1
                return
            }
            // Deleting the folder selected in the tree moves the selection to
            // its parent.
            root.selectedFolderId = info.parentId > 0 ? info.parentId : BookmarkManager.otherFolderId()
        }
    }

    FileDialog {
        id: importDialog
        title: qsTr("Import Bookmarks")
        fileMode: FileDialog.OpenFile
        nameFilters: ["HTML (*.html *.htm)"]
        onAccepted: BookmarkManager.importHtml(selectedFile)
    }
}
