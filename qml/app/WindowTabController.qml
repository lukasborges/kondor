import QtQuick
import Kondor

Item {
    id: root

    required property TabModel tabs
    required property var browserWindow
    required property var navigationBar

    function isLastTab() {
        return tabs.count <= 1
    }

    function closeTabAt(index) {
        if (isLastTab())
            browserWindow.close()
        else
            tabs.closeTab(index)
    }

    function closeTabFor(tab) {
        if (isLastTab())
            browserWindow.close()
        else
            tabs.closeTabObject(tab)
    }

    function activateTabAt(index) {
        if (index >= 0 && index < tabs.count)
            tabs.setCurrentIndex(index)
    }

    function stepTab(delta) {
        if (tabs.count < 2)
            return
        tabs.setCurrentIndex((tabs.currentIndex + delta + tabs.count) % tabs.count)
    }

    function openNewTab(isPrivate) {
        tabs.addTab(isPrivate || browserWindow.privateWindow)
        navigationBar.clearAddressBar()
        Qt.callLater(navigationBar.focusAddressBar)
    }

    function moveTabToNewWindow(tab) {
        if (!tab)
            return
        const url = tab.newTabPage ? "" : tab.url.toString()
        if (WindowManager.newWindow(tab.isPrivate, [url]))
            closeTabFor(tab)
    }

    function moveCurrentTab(delta) {
        const from = tabs.currentIndex
        const to = from + delta
        if (canMoveTab(from, to))
            tabs.moveTab(from, to)
    }

    function canMoveTab(from, to) {
        const tab = tabs.currentTab
        if (!tab || from < 0 || to < 0 || to >= tabs.count)
            return false
        return tab.pinned ? to < tabs.pinnedCount : to >= tabs.pinnedCount
    }

    function openTabContextMenu(tab, scenePosition) {
        const point = mapFromItem(null, scenePosition.x, scenePosition.y)
        tabContextMenu.tab = tab
        tabContextMenu.tabIndex = tabs.indexOfTab(tab)
        tabContextMenu.x = point.x
        tabContextMenu.y = point.y
        tabContextMenu.open()
    }

    function openUrlsInNewTabs(urls) {
        for (let i = 0; i < urls.length; ++i)
            tabs.addTab(browserWindow.privateWindow, urls[i])
    }

    function openUrl(url, background) {
        if (!url)
            return
        const tab = tabs.currentTab
        if (!tab)
            tabs.addTab(false, url)
        else if (background)
            openBackgroundTab(tab, url)
        else
            tab.navigateTo(url)
    }

    function openBackgroundTab(tab, url) {
        const profile = tab.isPrivate ? ProfileManager.createPrivateProfile()
                                      : ProfileManager.defaultProfile()
        tabs.addTabWithProfile(profile, url, true)
    }

    function homeUrl() {
        const isBlank = Settings.homePage.trim().length === 0
        return browserWindow.privateWindow || isBlank ? "" : Settings.homePage
    }

    function initialTitleAt(index) {
        const titles = browserWindow.initialTitles
        return index < titles.length ? titles[index] : ""
    }

    function restoreTab(index) {
        const tab = tabs.addTab(browserWindow.privateWindow, browserWindow.initialUrls[index])
        const title = initialTitleAt(index)
        if (tab && title.length > 0 && !tab.newTabPage)
            tab.setTitle(title)
    }

    function selectInitialTab() {
        const index = browserWindow.initialCurrentIndex
        if (index >= 0 && index < tabs.count)
            tabs.setCurrentIndex(index)
    }

    function restoreTabs() {
        for (let i = 0; i < browserWindow.initialUrls.length; ++i)
            restoreTab(i)
        selectInitialTab()
    }

    function openInitialTabs() {
        SessionManager.watch(tabs)
        if (browserWindow.initialUrls.length > 0)
            restoreTabs()
        else
            tabs.addTab(browserWindow.privateWindow, homeUrl())
    }

    Component.onCompleted: openInitialTabs()

    TabContextMenu {
        id: tabContextMenu
        tabModel: root.tabs
        targetWindow: root.browserWindow
        onNewTabRequested: root.openNewTab(false)
        onMoveToNewWindowRequested: root.moveTabToNewWindow(tabContextMenu.tab)
    }
}
