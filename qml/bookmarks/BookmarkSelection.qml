import QtQuick
import Kondor

QtObject {
    id: root

    required property TabModel tabModel
    required property var itemModel
    required property string filter

    property var folderId: BookmarkManager.otherFolderId()
    property var itemId: -1

    signal rowMoved(int row)

    onFolderIdChanged: root.itemId = -1

    function selectFolder(id) {
        root.itemId = -1
        root.folderId = id
    }

    function releaseItemMovedTo(id, targetFolderId) {
        if (root.itemId === id && targetFolderId !== root.folderId)
            root.itemId = -1
    }

    function selectedInfo() {
        const revision = BookmarkManager.revision
        return revision >= 0 ? BookmarkManager.bookmark(root.folderId) : {}
    }

    function hasItemSelection() {
        const revision = BookmarkManager.revision
        if (revision < 0 || !(root.itemId > 0))
            return false
        return BookmarkManager.bookmark(root.itemId).id > 0
    }

    function currentItemInfo() {
        return root.hasItemSelection() ? BookmarkManager.bookmark(root.itemId) : {}
    }

    function actionTarget() {
        return root.hasItemSelection() ? root.currentItemInfo() : root.selectedInfo()
    }

    function actionIsFolder() {
        return root.hasItemSelection() ? root.currentItemInfo().isFolder : true
    }

    function openBookmark(url, background) {
        if (!url)
            return
        const tab = root.tabModel.currentTab
        if (!tab)
            root.tabModel.addTab(false, url)
        else if (background)
            root.openInBackground(url, tab)
        else
            tab.navigateTo(url)
    }

    function openInBackground(url, tab) {
        const profile = tab.isPrivate ? ProfileManager.createPrivateProfile()
                                      : ProfileManager.defaultProfile()
        root.tabModel.addTabWithProfile(profile, url, true)
    }

    function openCurrentItem() {
        const info = root.currentItemInfo()
        if (!info.id)
            return
        if (info.isFolder)
            root.folderId = info.id
        else
            root.openBookmark(info.url)
    }

    function moveSelected(delta) {
        const info = root.actionTarget()
        if (root.filter.length > 0 || !info.id || info.special)
            return
        const isPicked = root.hasItemSelection()
        BookmarkManager.move(info.id, isPicked ? root.folderId : info.parentId, info.position + delta)
        if (isPicked)
            root.reportRowOf(info.id)
    }

    function reportRowOf(id) {
        const row = root.itemModel ? root.itemModel.rowOf(id) : -1
        if (row >= 0)
            root.rowMoved(row)
    }
}
