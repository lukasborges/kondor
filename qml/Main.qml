import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ApplicationWindow {
    id: window
    width: 1280
    height: 820
    minimumWidth: 640
    minimumHeight: 480
    visible: true
    title: {
        const t = tabs.currentTab
        if (!t)
            return Qt.application.displayName
        if (t.newTabPage)
            return (t.isPrivate ? qsTr("New Private Tab") : qsTr("New Tab"))
                   + " — " + Qt.application.displayName
        return (t.title.length) ? t.title + " — " + Qt.application.displayName
                                : Qt.application.displayName
    }

    TabModel {
        id: tabs
    }

    // Set once the user confirms quitting with downloads still running, so the
    // confirmation is not asked again on the retried close.
    property bool quitConfirmed: false

    onClosing: function(close) {
        // Save while the tabs still exist: closing the last tab closes the
        // window before TabModel removes it.
        SessionManager.save(tabs)
        if (DownloadManager.hasActiveDownloads && !window.quitConfirmed) {
            close.accepted = false
            quitDialog.open()
        }
    }

    MessageDialog {
        id: quitDialog
        //: %1 is the application name
        title: qsTr("Quit %1").arg(Qt.application.displayName)
        text: qsTr("Downloads are still in progress. Quit anyway?")
        buttons: MessageDialog.Yes | MessageDialog.No
        onAccepted: {
            window.quitConfirmed = true
            window.close()
        }
    }

    function closeTabAt(idx) {
        if (tabs.count <= 1) {
            window.close()
            return
        }
        tabs.closeTab(idx)
    }

    function closeTabFor(t) {
        if (tabs.count <= 1) {
            window.close()
            return
        }
        tabs.closeTabObject(t)
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

    // Every "new tab" entry point goes through here: open the tab and focus the
    // address bar. Deferred like the Ctrl+F fix, so the page cannot take the
    // focus back while the shortcut key event is still being handled.
    function openNewTab(isPrivate) {
        tabs.addTab(isPrivate)
        // syncFromTab() leaves the field alone while it has focus, so clear it
        // here: a New Tab page has no address to show.
        addressBar.text = ""
        Qt.callLater(function() {
            addressBar.forceActiveFocus()
            addressBar.selectAll()
        })
    }

    // True when the scene point is on the empty part of the tab bar, not on a
    // tab or on the new-tab button.
    function emptyTabBarAt(sceneX, sceneY) {
        const buttonPoint = newTabButton.mapFromItem(null, sceneX, sceneY)
        if (buttonPoint.x >= 0 && buttonPoint.x <= newTabButton.width
                && buttonPoint.y >= 0 && buttonPoint.y <= newTabButton.height)
            return false
        if (tabBar.contentItem) {
            const point = tabBar.contentItem.mapFromItem(null, sceneX, sceneY)
            if (point.x <= tabBar.contentItem.contentWidth)
                return false
        }
        return true
    }

    function moveCurrentTab(delta) {
        const from = tabs.currentIndex
        const tab = tabs.currentTab
        if (!tab || from < 0)
            return
        const to = from + delta
        if (to < 0 || to >= tabs.count)
            return
        // Pinned and unpinned tabs stay in their own groups.
        if (tab.pinned ? to >= tabs.pinnedCount : to < tabs.pinnedCount)
            return
        tabs.moveTab(from, to)
    }

    function openTabContextMenu(tab, scenePosition) {
        tabContextMenu.tab = tab
        tabContextMenu.tabIndex = tabs.indexOfTab(tab)
        const point = contentItem.mapFromItem(null, scenePosition.x, scenePosition.y)
        tabContextMenu.x = point.x
        tabContextMenu.y = point.y
        tabContextMenu.open()
    }

    TabContextMenu {
        id: tabContextMenu
        tabModel: tabs
        targetWindow: window
        onNewTabRequested: window.openNewTab(false)
    }

    // FileDialog hands a file:// URL to QML; downloads need a local path.
    function localPath(url) {
        let path = url.toString()
        if (path.startsWith("file://"))
            path = path.slice(7)
        return decodeURIComponent(path)
    }

    function openHistory() {
        if (!historyWindow)
            historyWindow = historyWindowComponent.createObject(window)
        historyWindow.showWindow()
    }

    function openSettings() {
        if (!settingsWindow)
            settingsWindow = settingsWindowComponent.createObject(window)
        settingsWindow.showWindow()
    }

    function openBookmarks() {
        if (!bookmarksWindow)
            bookmarksWindow = bookmarksWindowComponent.createObject(window)
        bookmarksWindow.showWindow()
    }

    // Normal click navigates the current tab; middle/Ctrl+click opens a
    // background tab (in a private profile when the current tab is private).
    function openBookmark(url, background) {
        if (!url)
            return
        const tab = tabs.currentTab
        if (!tab) {
            tabs.addTab(false, url)
        } else if (background) {
            const profile = tab.isPrivate ? ProfileManager.createPrivateProfile()
                                          : ProfileManager.defaultProfile()
            tabs.addTabWithProfile(profile, url, true)
        } else {
            tab.navigateTo(url)
        }
    }

    // Star button and Ctrl+D: add the page to "Other Bookmarks" (the first
    // time) and open the edit popup.
    function openBookmarkEditor() {
        const tab = tabs.currentTab
        if (!tab || tab.newTabPage || tab.url.toString().length === 0)
            return

        let id = BookmarkManager.bookmarkIdFor(tab.url)
        let added = false
        if (id <= 0) {
            id = BookmarkManager.addBookmark(tab.url, tab.title, BookmarkManager.otherFolderId())
            if (id <= 0)
                return
            added = true
        }

        const info = BookmarkManager.bookmark(id)
        bookmarkPopup.editingId = id
        bookmarkPopup.justAdded = added
        bookmarkTitleField.text = info.title
        bookmarkFolderBox.model = BookmarkManager.folders
        let index = 0
        const folders = bookmarkFolderBox.model
        for (let i = 0; i < folders.length; ++i) {
            if (folders[i].id === info.parentId) {
                index = i
                break
            }
        }
        bookmarkFolderBox.currentIndex = index
        bookmarkPopup.open()
    }

    function saveBookmark() {
        if (bookmarkPopup.editingId <= 0)
            return
        const title = bookmarkTitleField.text.trim()
        if (title.length > 0)
            BookmarkManager.rename(bookmarkPopup.editingId, title)
        const folders = bookmarkFolderBox.model
        const index = bookmarkFolderBox.currentIndex
        if (index >= 0 && index < folders.length) {
            const info = BookmarkManager.bookmark(bookmarkPopup.editingId)
            if (info.parentId !== folders[index].id)
                BookmarkManager.move(bookmarkPopup.editingId, folders[index].id, -1)
        }
        bookmarkPopup.close()
    }

    function removeBookmark() {
        if (bookmarkPopup.editingId > 0)
            BookmarkManager.remove(bookmarkPopup.editingId)
        bookmarkPopup.close()
    }

    readonly property bool pageBookmarked: {
        const revision = BookmarkManager.revision
        const tab = tabs.currentTab
        return revision >= 0 && tab !== null && tab.url.toString().length > 0
            && BookmarkManager.isBookmarked(tab.url)
    }

    Component.onCompleted: {
        SessionManager.watch(tabs)
        if (Settings.startupBehavior === "restore")
            SessionManager.restore(tabs)
        for (let i = 0; i < StartupArgs.startupUrls.length; ++i)
            tabs.addTab(StartupArgs.startupPrivate, StartupArgs.startupUrls[i])
        // "kondor --private" (desktop action "New Private Window") still needs
        // its private tab when there is no URL and a session was restored.
        // The fallback tab loads the home page; a blank home page means the New
        // Tab page, which is also what a private tab shows.
        if (tabs.count === 0 || (StartupArgs.startupPrivate && StartupArgs.startupUrls.length === 0))
            tabs.addTab(StartupArgs.startupPrivate,
                        StartupArgs.startupPrivate ? "" : Settings.homePage)
    }

    header: ColumnLayout {
        spacing: 0

        // ── Tab bar ──────────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: tabBar.implicitHeight
            Kirigami.Theme.colorSet: Kirigami.Theme.Header
            Kirigami.Theme.inherit: false
            color: Kirigami.Theme.backgroundColor

            RowLayout {
                id: tabBarRow
                anchors.fill: parent
                spacing: 0

                TabBar {
                    id: tabBar
                    // Let the bar shrink when the tabs no longer fit; after the
                    // minimum width the internal ListView scrolls.
                    Layout.minimumWidth: 0
                    // Room left for the tabs once the new-tab button is placed.
                    readonly property real tabsAreaWidth: Math.max(90, tabBarRow.width - newTabButton.implicitWidth - 10)
                    Layout.maximumWidth: tabsAreaWidth
                    // Index a dragged tab would land on; drives the drop indicator.
                    property int dropTargetIndex: -1

                    currentIndex: tabs.currentIndex
                    background: null

                    onCurrentIndexChanged: {
                        if (tabs.currentIndex !== currentIndex)
                            tabs.setCurrentIndex(currentIndex)
                    }

                    Component.onCompleted: {
                        // Let the internal ListView flick when the tabs overflow.
                        if (contentItem)
                            contentItem.interactive = true
                    }

                    Repeater {
                        model: tabs

                        delegate: TabButtonDelegate {
                            tabModel: tabs
                            tabBarItem: tabBar
                            targetWindow: window
                            tabCount: tabs.count
                            pinnedCount: tabs.pinnedCount
                            tabsAreaWidth: tabBar.tabsAreaWidth
                        }
                    }

                    // A mouse wheel over the tab bar scrolls it horizontally.
                    WheelHandler {
                        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                        onWheel: function(event) {
                            const view = tabBar.contentItem
                            if (!view)
                                return
                            const maximum = Math.max(0, view.contentWidth - view.width)
                            if (maximum <= 0)
                                return

                            const delta = event.pixelDelta.x !== 0 ? event.pixelDelta.x
                                : event.pixelDelta.y !== 0 ? -event.pixelDelta.y
                                : event.angleDelta.x !== 0 ? event.angleDelta.x
                                : -event.angleDelta.y
                            view.contentX = Math.max(0, Math.min(maximum, view.contentX + delta))
                        }
                    }
                }

                // New-tab button, right after the last tab.
                ToolButton {
                    id: newTabButton
                    Layout.alignment: Qt.AlignVCenter
                    Layout.leftMargin: 2
                    Layout.minimumWidth: implicitWidth
                    display: AbstractButton.IconOnly
                    icon.name: "tab-new"
                    icon.width: 16
                    icon.height: 16
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("New Tab")
                    ToolTip.delay: 600
                    onClicked: window.openNewTab(false)
                }

                Item { Layout.fillWidth: true }
            }

            // Where a dragged tab will land.
            Rectangle {
                readonly property Item targetItem: tabBar.dropTargetIndex >= 0 && tabBar.contentItem
                    ? tabBar.itemAt(tabBar.dropTargetIndex) : null
                visible: targetItem !== null
                x: tabBar.x + (targetItem ? targetItem.x - tabBar.contentItem.contentX : 0)
                y: tabBar.y
                width: 2
                height: tabBar.height
                color: Kirigami.Theme.highlightColor
            }

            // Double-click (or middle click) on the empty part of the tab bar
            // opens a new tab.
            TapHandler {
                acceptedButtons: Qt.LeftButton
                onDoubleTapped: function(eventPoint) {
                    if (window.emptyTabBarAt(eventPoint.scenePosition.x,
                                             eventPoint.scenePosition.y))
                        window.openNewTab(false)
                }
            }

            TapHandler {
                acceptedButtons: Qt.MiddleButton
                onTapped: function(eventPoint) {
                    if (window.emptyTabBarAt(eventPoint.scenePosition.x,
                                             eventPoint.scenePosition.y))
                        window.openNewTab(false)
                }
            }
        }

        // ── Navigation bar ───────────────────────────────────────────────
        ToolBar {
            Layout.fillWidth: true
            // Same color as the active tab / window background.
            Kirigami.Theme.colorSet: Kirigami.Theme.Window
            Kirigami.Theme.inherit: false

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 5
                anchors.rightMargin: 5
                spacing: 2

                ToolButton {
                    display: AbstractButton.IconOnly
                    icon.name: "go-previous"
                    enabled: tabs.currentTab ? tabs.currentTab.canGoBack : false
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Back")
                    ToolTip.delay: 600
                    onClicked: {
                        if (tabs.currentTab)
                            tabs.currentTab.goBack()
                    }
                }

                ToolButton {
                    display: AbstractButton.IconOnly
                    icon.name: "go-next"
                    enabled: tabs.currentTab ? tabs.currentTab.canGoForward : false
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Forward")
                    ToolTip.delay: 600
                    onClicked: {
                        if (tabs.currentTab)
                            tabs.currentTab.goForward()
                    }
                }

                ToolButton {
                    display: AbstractButton.IconOnly
                    icon.name: (tabs.currentTab && tabs.currentTab.loading) ? "process-stop" : "view-refresh"
                    enabled: tabs.currentTab ? !tabs.currentTab.newTabPage : false
                    ToolTip.visible: hovered
                    ToolTip.text: (tabs.currentTab && tabs.currentTab.loading) ? qsTr("Stop") : qsTr("Reload")
                    ToolTip.delay: 600
                    onClicked: {
                        if (!tabs.currentTab)
                            return
                        if (tabs.currentTab.loading)
                            tabs.currentTab.stop()
                        else
                            tabs.currentTab.reload()
                    }
                }

                ToolButton {
                    display: AbstractButton.IconOnly
                    icon.name: "go-home"
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Home")
                    ToolTip.delay: 600
                    onClicked: {
                        if (!tabs.currentTab)
                            return
                        if (Settings.homePage.trim().length === 0)
                            tabs.currentTab.showNewTabPage()
                        else
                            tabs.currentTab.navigateTo(ProfileManager.resolveAddress(""))
                    }
                }

                TextField {
                    id: addressBar
                    Layout.fillWidth: true
                    Layout.leftMargin: 8
                    Layout.rightMargin: 8
                    placeholderText: qsTr("Search or enter address")
                    selectByMouse: true
                    rightPadding: bookmarkButton.visible ? bookmarkButton.width + 10 : 8

                    function syncFromTab() {
                        if (activeFocus)
                            return
                        const t = tabs.currentTab
                        // The New Tab page has no address of its own.
                        text = (t && !t.newTabPage) ? t.url.toString() : ""
                    }

                    onAccepted: {
                        const t = tabs.currentTab
                        if (!t)
                            return
                        if (addressSuggestions.opened) {
                            addressSuggestions.activate(addressSuggestions.currentIndex)
                            return
                        }
                        t.navigateTo(ProfileManager.resolveAddress(text))
                        focus = false
                    }

                    onTextEdited: {
                        addressSuggestions.text = text
                        if (addressSuggestions.rows.length > 0) {
                            addressSuggestions.currentIndex = 0
                            addressSuggestions.open()
                        } else {
                            addressSuggestions.close()
                        }
                    }

                    Keys.onDownPressed: function(event) {
                        if (!addressSuggestions.opened) {
                            event.accepted = false
                            return
                        }
                        addressSuggestions.currentIndex =
                            Math.min(addressSuggestions.currentIndex + 1,
                                     addressSuggestions.rows.length - 1)
                        event.accepted = true
                    }

                    Keys.onUpPressed: function(event) {
                        if (!addressSuggestions.opened) {
                            event.accepted = false
                            return
                        }
                        addressSuggestions.currentIndex =
                            Math.max(addressSuggestions.currentIndex - 1, 0)
                        event.accepted = true
                    }

                    Keys.onEscapePressed: function(event) {
                        if (!addressSuggestions.opened) {
                            event.accepted = false
                            return
                        }
                        // Only the dropdown goes away; the typed text stays.
                        addressSuggestions.close()
                        event.accepted = true
                    }

                    onActiveFocusChanged: {
                        if (activeFocus) {
                            selectAll()
                        } else {
                            addressSuggestions.close()
                        }
                    }

                    Component.onCompleted: syncFromTab()

                    Row {
                        id: bookmarkSlot
                        anchors.right: parent.right
                        anchors.rightMargin: 3
                        anchors.verticalCenter: parent.verticalCenter

                        ToolButton {
                            id: bookmarkButton
                            visible: tabs.currentTab && tabs.currentTab.url.toString().length > 0
                            enabled: tabs.currentTab ? !tabs.currentTab.newTabPage : false
                            display: AbstractButton.IconOnly
                            icon.name: window.pageBookmarked ? "bookmarks-bookmarked" : "bookmarks"
                            icon.width: 16
                            icon.height: 16
                            flat: true
                            implicitWidth: 28
                            implicitHeight: 28
                            ToolTip.visible: hovered
                            ToolTip.text: window.pageBookmarked ? qsTr("Edit This Bookmark") : qsTr("Bookmark This Page")
                            ToolTip.delay: 600
                            onClicked: {
                                if (bookmarkPopup.opened)
                                    bookmarkPopup.close()
                                else
                                    window.openBookmarkEditor()
                            }
                        }
                    }

                    AddressSuggestions {
                        id: addressSuggestions
                        x: 0
                        y: addressBar.height
                        width: addressBar.width

                        onNavigate: function(url) {
                            if (tabs.currentTab)
                                tabs.currentTab.navigateTo(url)
                            addressSuggestions.close()
                            addressBar.focus = false
                        }
                    }
                }

                ToolButton {
                    id: downloadsButton
                    visible: DownloadManager.model.count > 0
                    display: AbstractButton.IconOnly
                    icon.name: "download"
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Downloads")
                    ToolTip.delay: 600
                    onClicked: downloadsPopup.opened ? downloadsPopup.close() : downloadsPopup.open()

                    ProgressBar {
                        anchors {
                            left: parent.left
                            right: parent.right
                            bottom: parent.bottom
                            margins: 4
                        }
                        height: 2
                        visible: DownloadManager.hasActiveDownloads
                        value: DownloadManager.activeProgress >= 0 ? DownloadManager.activeProgress : 0
                        indeterminate: DownloadManager.activeProgress < 0
                    }

                    DownloadsPopup {
                        id: downloadsPopup
                        x: downloadsButton.width - width
                        y: downloadsButton.height
                    }
                }

                ToolButton {
                    id: menuButton
                    display: AbstractButton.IconOnly
                    icon.name: "application-menu"
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Menu")
                    ToolTip.delay: 600
                    onClicked: mainMenu.open()

                    Menu {
                        id: mainMenu

                        MenuItem {
                            text: qsTr("New Tab")
                            icon.name: "tab-new"
                            onTriggered: window.openNewTab(false)
                        }
                        MenuItem {
                            text: qsTr("New Private Tab")
                            icon.name: "view-private"
                            onTriggered: window.openNewTab(true)
                        }
                        MenuItem {
                            text: qsTr("Reopen Closed Tab")
                            icon.name: "edit-undo"
                            enabled: tabs.canReopenClosedTab
                            onTriggered: tabs.reopenClosedTab()
                        }
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("Close Tab")
                            icon.name: "window-close"
                            onTriggered: window.closeTabAt(tabs.currentIndex)
                        }
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("Find in Page…")
                            icon.name: "edit-find"
                            enabled: tabs.currentTab ? !tabs.currentTab.newTabPage : false
                            onTriggered: findBar.open()
                        }
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("Zoom In")
                            icon.name: "zoom-in"
                            enabled: tabs.currentTab ? !tabs.currentTab.newTabPage : false
                            onTriggered: {
                                if (tabs.currentTab)
                                    tabs.currentTab.zoomIn()
                            }
                        }
                        MenuItem {
                            text: qsTr("Zoom Out")
                            icon.name: "zoom-out"
                            enabled: tabs.currentTab ? !tabs.currentTab.newTabPage : false
                            onTriggered: {
                                if (tabs.currentTab)
                                    tabs.currentTab.zoomOut()
                            }
                        }
                        MenuItem {
                            text: qsTr("Actual Size")
                            icon.name: "zoom-original"
                            enabled: tabs.currentTab ? !tabs.currentTab.newTabPage : false
                            onTriggered: {
                                if (tabs.currentTab)
                                    tabs.currentTab.resetZoom()
                            }
                        }
                        MenuSeparator {}
                        BookmarkMenu {
                            title: qsTr("Bookmarks")
                            icon.name: "bookmarks"
                            showCommands: true
                            folderId: BookmarkManager.toolbarFolderId()
                            onBookmarkActivated: function(url, background) {
                                window.openBookmark(url, background)
                            }
                            onBookmarkThisPageRequested: window.openBookmarkEditor()
                            onManageBookmarksRequested: window.openBookmarks()
                        }
                        MenuItem {
                            text: qsTr("History")
                            icon.name: "view-history"
                            onTriggered: window.openHistory()
                        }
                        MenuSeparator {}
                        MenuItem {
                            //: %1 is the application name
                            text: qsTr("Configure %1…").arg(Qt.application.displayName)
                            icon.name: "configure"
                            onTriggered: window.openSettings()
                        }
                        MenuSeparator {}
                        MenuItem {
                            //: %1 is the application name
                            text: qsTr("About %1").arg(Qt.application.displayName)
                            icon.name: "help-about"
                        }
                    }
                }
            }
        }

        // ── Bookmarks bar ────────────────────────────────────────────────
        BookmarksBar {
            Layout.fillWidth: true
            tabModel: tabs
        }
    }

    // ── Content area: one WebEngineView per tab ─────────────────────────
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        FindBar {
            id: findBar
            tab: tabs.currentTab
            Layout.fillWidth: true
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: window.palette.base

            Repeater {
                model: tabs

                delegate: WebViewTab {
                    tabModel: tabs
                    anchors.fill: parent
                    visible: tabs.currentTab === tab
                }
            }
        }
    }

    // ── History window (created on demand) ──────────────────────────────
    property var historyWindow: null

    Component {
        id: historyWindowComponent
        HistoryWindow {
            tabModel: tabs
        }
    }

    // ── Settings window (created on demand) ─────────────────────────────
    property var settingsWindow: null

    Component {
        id: settingsWindowComponent
        SettingsWindow {
            tabModel: tabs
        }
    }

    // ── Bookmarks manager (created on demand) ───────────────────────────
    property var bookmarksWindow: null

    Component {
        id: bookmarksWindowComponent
        BookmarksWindow {
            tabModel: tabs
        }
    }

    // ── Star button popup: name and folder of the current page ──────────
    Popup {
        id: bookmarkPopup
        parent: bookmarkButton
        x: bookmarkButton.width - width
        y: bookmarkButton.height
        width: Kirigami.Units.gridUnit * 20
        padding: Kirigami.Units.largeSpacing

        property var editingId: -1
        property bool justAdded: false

        contentItem: ColumnLayout {
            spacing: Kirigami.Units.largeSpacing

            Kirigami.Heading {
                level: 4
                text: bookmarkPopup.justAdded ? qsTr("Page bookmarked") : qsTr("Edit Bookmark")
            }

            Kirigami.FormLayout {
                Layout.fillWidth: true

                TextField {
                    id: bookmarkTitleField
                    Kirigami.FormData.label: qsTr("Name:")
                    Layout.fillWidth: true
                }

                ComboBox {
                    id: bookmarkFolderBox
                    Kirigami.FormData.label: qsTr("Folder:")
                    Layout.fillWidth: true
                    textRole: "title"
                }
            }

            RowLayout {
                Layout.fillWidth: true

                Button {
                    text: qsTr("Remove")
                    icon.name: "edit-delete"
                    onClicked: window.removeBookmark()
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: qsTr("Done")
                    icon.name: "dialog-ok-apply"
                    highlighted: true
                    onClicked: window.saveBookmark()
                }
            }
        }
    }

    // ── Save dialog for "Ask where to save each file" ───────────────────
    FileDialog {
        id: saveFileDialog
        title: qsTr("Save File")
        fileMode: FileDialog.SaveFile
        property var pendingDownload: null

        onAccepted: {
            if (!pendingDownload)
                return
            const path = window.localPath(selectedFile)
            const slash = path.lastIndexOf("/")
            if (slash > 0) {
                pendingDownload.downloadDirectory = path.slice(0, slash)
                pendingDownload.downloadFileName = path.slice(slash + 1)
            }
            pendingDownload.accept()
            pendingDownload = null
        }

        onRejected: {
            if (pendingDownload)
                pendingDownload.cancel()
            pendingDownload = null
        }
    }

    Connections {
        target: DownloadManager

        function onSaveLocationRequested(request, suggestedFile) {
            saveFileDialog.pendingDownload = request
            saveFileDialog.currentFile = suggestedFile
            saveFileDialog.open()
        }

        function onDownloadStarted() {
            downloadsPopup.open()
        }
    }

    Connections {
        target: DownloadManager.model

        function onCountChanged() {
            // The button (and so the popup's anchor) disappears when the list
            // becomes empty; do not leave the popup floating around.
            if (DownloadManager.model.count === 0)
                downloadsPopup.close()
        }
    }

    // ── Shortcuts ───────────────────────────────────────────────────────
    Shortcut {
        sequence: "Ctrl+T"
        onActivated: window.openNewTab(false)
    }
    Shortcut {
        sequence: "Ctrl+Shift+N"
        onActivated: window.openNewTab(true)
    }
    Shortcut {
        sequence: "Ctrl+W"
        onActivated: window.closeTabAt(tabs.currentIndex)
    }
    Shortcut {
        sequence: "Ctrl+Shift+T"
        onActivated: tabs.reopenClosedTab()
    }
    Shortcut {
        sequences: ["Ctrl+Tab", "Ctrl+PgDown"]
        onActivated: window.stepTab(1)
    }
    Shortcut {
        sequences: ["Ctrl+Shift+Tab", "Ctrl+PgUp"]
        onActivated: window.stepTab(-1)
    }
    Shortcut {
        sequence: "Ctrl+1"
        onActivated: window.activateTabAt(0)
    }
    Shortcut {
        sequence: "Ctrl+2"
        onActivated: window.activateTabAt(1)
    }
    Shortcut {
        sequence: "Ctrl+3"
        onActivated: window.activateTabAt(2)
    }
    Shortcut {
        sequence: "Ctrl+4"
        onActivated: window.activateTabAt(3)
    }
    Shortcut {
        sequence: "Ctrl+5"
        onActivated: window.activateTabAt(4)
    }
    Shortcut {
        sequence: "Ctrl+6"
        onActivated: window.activateTabAt(5)
    }
    Shortcut {
        sequence: "Ctrl+7"
        onActivated: window.activateTabAt(6)
    }
    Shortcut {
        sequence: "Ctrl+8"
        onActivated: window.activateTabAt(7)
    }
    Shortcut {
        sequence: "Ctrl+9"
        onActivated: window.activateTabAt(tabs.count - 1)
    }
    Shortcut {
        sequence: "Ctrl+Shift+PgUp"
        onActivated: window.moveCurrentTab(-1)
    }
    Shortcut {
        sequence: "Ctrl+Shift+PgDown"
        onActivated: window.moveCurrentTab(1)
    }
    Shortcut {
        sequence: "Ctrl+L"
        onActivated: {
            addressBar.forceActiveFocus()
            addressBar.selectAll()
        }
    }
    Shortcut {
        sequence: "Ctrl+H"
        onActivated: window.openHistory()
    }
    Shortcut {
        sequence: "Ctrl+D"
        onActivated: window.openBookmarkEditor()
    }
    Shortcut {
        sequence: "Ctrl+Shift+B"
        onActivated: Settings.showBookmarksBar = !Settings.showBookmarksBar
    }
    Shortcut {
        sequence: "Ctrl+Shift+O"
        onActivated: window.openBookmarks()
    }
    Shortcut {
        sequences: [StandardKey.Preferences, "Ctrl+,"]
        onActivated: window.openSettings()
    }
    Shortcut {
        sequences: ["F5", "Ctrl+R"]
        onActivated: {
            if (tabs.currentTab && !tabs.currentTab.newTabPage)
                tabs.currentTab.reload()
        }
    }
    Shortcut {
        sequences: ["Alt+Left"]
        onActivated: {
            if (tabs.currentTab)
                tabs.currentTab.goBack()
        }
    }
    Shortcut {
        sequences: ["Alt+Right"]
        onActivated: {
            if (tabs.currentTab)
                tabs.currentTab.goForward()
        }
    }
    Shortcut {
        sequences: ["Ctrl++", "Ctrl+="]
        onActivated: {
            if (tabs.currentTab && !tabs.currentTab.newTabPage)
                tabs.currentTab.zoomIn()
        }
    }
    Shortcut {
        sequences: ["Ctrl+-"]
        onActivated: {
            if (tabs.currentTab && !tabs.currentTab.newTabPage)
                tabs.currentTab.zoomOut()
        }
    }
    Shortcut {
        sequence: "Ctrl+0"
        onActivated: {
            if (tabs.currentTab && !tabs.currentTab.newTabPage)
                tabs.currentTab.resetZoom()
        }
    }
    Shortcut {
        sequences: [StandardKey.Find]
        enabled: tabs.currentTab ? !tabs.currentTab.newTabPage : false
        onActivated: findBar.open()
    }
    Shortcut {
        sequence: "F3"
        enabled: findBar.visible
        onActivated: findBar.findNext()
    }
    Shortcut {
        sequence: "Shift+F3"
        enabled: findBar.visible
        onActivated: findBar.findPrevious()
    }

    Connections {
        target: tabs
        function onCurrentIndexChanged() {
            if (tabBar.currentIndex !== tabs.currentIndex)
                tabBar.currentIndex = tabs.currentIndex
            // Keep the current tab visible when the tab bar overflows.
            if (tabs.currentIndex >= 0 && tabBar.contentItem) {
                tabBar.contentItem.positionViewAtIndex(tabs.currentIndex, ListView.Contain)
            }
        }
        function onCurrentTabChanged() {
            addressSuggestions.close()
            addressBar.syncFromTab()
        }
    }

    Connections {
        target: tabs.currentTab
        function onUrlChanged() {
            addressBar.syncFromTab()
        }
        function onNewTabPageChanged() {
            addressBar.syncFromTab()
        }
    }
}
