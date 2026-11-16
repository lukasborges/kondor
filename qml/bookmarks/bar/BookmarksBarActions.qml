import QtQuick
import Kondor

QtObject {
    id: root

    required property TabModel tabModel

    readonly property var currentTab: root.tabModel ? root.tabModel.currentTab : null
    readonly property bool canAddBookmarks: root.currentTab !== null && !root.currentTab.isPrivate
    readonly property bool isPageBookmarkable: root.currentTab !== null && !root.currentTab.newTabPage
                                               && root.currentTab.url.toString().length > 0

    function openBookmark(url, background) {
        if (!url || !root.currentTab)
            return
        if (background)
            root.openInNewTab(url, true)
        else
            root.currentTab.navigateTo(url)
    }

    function openInNewTab(url, background) {
        const tab = root.currentTab
        if (!tab || !url)
            return
        const profile = tab.isPrivate ? ProfileManager.createPrivateProfile()
                                      : ProfileManager.defaultProfile()
        root.tabModel.addTabWithProfile(profile, url, background)
    }

    function openInNewWindow(url) {
        if (url && root.currentTab)
            WindowManager.newWindow(root.currentTab.isPrivate, [url])
    }

    function bookmarksIn(folderId) {
        return BookmarkManager.folderContents(folderId).filter(entry => !entry.isFolder)
    }

    function openAllIn(folderId) {
        root.bookmarksIn(folderId).reverse().forEach(entry => root.openInNewTab(entry.url, true))
    }

    function isPageIn(folderId) {
        const url = root.currentTab.url.toString()
        return root.bookmarksIn(folderId).some(entry => entry.url === url)
    }

    function canAddPageTo(folderId) {
        return root.canAddBookmarks && root.isPageBookmarkable && !root.isPageIn(folderId)
    }

    function addPageTo(folderId) {
        if (root.canAddPageTo(folderId))
            BookmarkManager.addBookmark(root.currentTab.url, root.currentTab.title, folderId)
    }
}
