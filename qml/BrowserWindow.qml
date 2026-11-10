import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window
import QtWebEngine
import org.kde.kirigami as Kirigami
import Kondor

// One browser window. WindowManager creates them (normal and private), each
// with its own TabModel; the main window is no longer special.
ApplicationWindow {
    id: window
    width: 1280
    height: 820
    minimumWidth: 640
    minimumHeight: 480
    visible: true

    // A private window opens every tab, including new ones, in a private
    // profile; nothing it shows is ever written to disk.
    property bool privateWindow: false

    // Tabs to open instead of the home page: one URL per tab, an empty URL for
    // the New Tab page. WindowManager fills them with the command-line URLs or
    // with a restored session.
    property var initialUrls: []
    property var initialTitles: []
    property int initialCurrentIndex: -1

    title: {
        const t = tabs.currentTab
        let base = Qt.application.displayName
        if (t) {
            if (t.newTabPage)
                base = (t.isPrivate ? qsTr("New Private Tab") : qsTr("New Tab"))
                       + " — " + Qt.application.displayName
            else if (t.title.length)
                base = t.title + " — " + Qt.application.displayName
        }
        return privateWindow ? base + " — " + qsTr("Private Browsing") : base
    }

    TabModel {
        id: tabs
        // A private window has only private tabs, however a tab is opened.
        privateTabs: window.privateWindow
    }

    // Set once the user confirms quitting with downloads still running, so the
    // confirmation is not asked again on the retried close.
    property bool quitConfirmed: false

    // Page full screen comes from the current tab (a video player); F11 turns
    // the whole window full screen and keeps the toolbars on screen.
    property bool pageFullScreen: tabs.currentTab ? tabs.currentTab.isFullScreen : false
    property bool windowFullScreen: false
    // Windowed or maximized state to return to when full screen ends.
    property int visibilityBeforeFullScreen: Window.Windowed

    function updateFullScreen() {
        if (pageFullScreen || windowFullScreen) {
            if (window.visibility !== Window.FullScreen)
                visibilityBeforeFullScreen = window.visibility
            window.showFullScreen()
        } else if (visibilityBeforeFullScreen === Window.Maximized) {
            window.showMaximized()
        } else {
            window.showNormal()
        }
    }

    onPageFullScreenChanged: {
        // Hidden chrome leaves no other clue, so say how to get out.
        if (pageFullScreen)
            fullScreenHint.show()
        else
            fullScreenHint.hide()
        updateFullScreen()
    }

    onWindowFullScreenChanged: updateFullScreen()

    onClosing: function(close) {
        // Save while the tabs still exist: closing the last tab closes the
        // window before TabModel removes it.
        SessionManager.save(tabs)
        // Only the last window quits the app; another one closing leaves the
        // downloads running.
        if (WindowManager.windowCount <= 1 && DownloadManager.hasActiveDownloads
                && !window.quitConfirmed) {
            close.accepted = false
            quitDialog.open()
            return
        }
        // A closed window is over: WindowManager drops it from the list and
        // deletes it, and the app quits when the last one is gone.
        WindowManager.closeWindow(window)
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

    function securityIconForState(state) {
        switch (state) {
        case "secure":
            return "security-high"
        case "insecure":
            return "security-medium"
        case "error":
            return "security-low"
        }
        return "text-html"
    }

    function stepTab(delta) {
        if (tabs.count < 2)
            return
        tabs.setCurrentIndex((tabs.currentIndex + delta + tabs.count) % tabs.count)
    }

    // Every "new tab" entry point goes through here: open the tab and focus the
    // address bar. Deferred like the Ctrl+F fix, so the page cannot take the
    // focus back while the shortcut key event is still being handled. In a
    // private window every tab is private, whatever the caller asked for.
    function openNewTab(isPrivate) {
        tabs.addTab(isPrivate || privateWindow)
        // syncFromTab() leaves the field alone while it has focus, so clear it
        // here: a New Tab page has no address to show.
        addressBar.text = ""
        Qt.callLater(function() {
            addressBar.forceActiveFocus()
            addressBar.selectAll()
        })
    }

    // The live WebEngineView cannot move between windows, so the page reloads
    // in a new window and the tab here closes.
    function moveTabToNewWindow(tab) {
        if (!tab)
            return
        const url = tab.newTabPage ? "" : tab.url.toString()
        if (!WindowManager.newWindow(tab.isPrivate, [url]))
            return
        closeTabFor(tab)
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
        onMoveToNewWindowRequested: window.moveTabToNewWindow(tabContextMenu.tab)
    }

    // FileDialog hands a file:// URL to QML; downloads need a local path.
    function localPath(url) {
        let path = url.toString()
        if (path.startsWith("file://"))
            path = path.slice(7)
        return decodeURIComponent(path)
    }

    readonly property bool canPrintOrSave: tabs.currentTab ? !tabs.currentTab.newTabPage : false

    function suggestedFile(extension) {
        return FileHelper.suggestedFileUrl(Settings.downloadDirectory,
                                           tabs.currentTab ? tabs.currentTab.title : "", extension)
    }

    function saveAsPdf() {
        if (!canPrintOrSave)
            return
        pdfDialog.currentFile = suggestedFile(".pdf")
        pdfDialog.open()
    }

    function savePageAs() {
        if (!canPrintOrSave)
            return
        pageDialog.currentFile = suggestedFile(".html")
        pageDialog.open()
    }

    function printPage() {
        if (canPrintOrSave)
            tabs.currentTab.print()
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

    function openAbout() {
        if (!aboutWindow)
            aboutWindow = aboutWindowComponent.createObject(window)
        aboutWindow.showWindow()
    }

    function openBookmarks() {
        if (!bookmarksWindow)
            bookmarksWindow = bookmarksWindowComponent.createObject(window)
        bookmarksWindow.showWindow()
    }

    function openSitePermissions() {
        if (!sitePermissionsWindow)
            sitePermissionsWindow = sitePermissionsComponent.createObject(window)
        sitePermissionsWindow.showWindow()
    }

    // A later `kondor` launch: one tab per URL, leaving the current page as it
    // is. WindowManager calls this through the single-instance handler.
    function openUrlsInNewTabs(urls) {
        for (let i = 0; i < urls.length; ++i)
            tabs.addTab(privateWindow, urls[i])
    }

    // Normal click navigates the current tab; middle/Ctrl+click opens a
    // background tab (in a private profile when the current tab is private).
    function openUrl(url, background) {
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
        if (initialUrls.length > 0) {
            for (let i = 0; i < initialUrls.length; ++i) {
                const tab = tabs.addTab(privateWindow, initialUrls[i])
                const title = i < initialTitles.length ? initialTitles[i] : ""
                // Restored tabs show their old title until the page loads.
                if (tab && title.length > 0 && !tab.newTabPage)
                    tab.setTitle(title)
            }
            if (initialCurrentIndex >= 0 && initialCurrentIndex < tabs.count)
                tabs.setCurrentIndex(initialCurrentIndex)
            return
        }
        // A private window has nothing to show from disk, so it starts on the
        // New Tab page; a normal one on the home page when it is set.
        tabs.addTab(privateWindow,
                    privateWindow || Settings.homePage.trim().length === 0 ? "" : Settings.homePage)
    }

    header: ColumnLayout {
        spacing: 0
        // A page in full screen takes the whole window, like a video player.
        visible: !window.pageFullScreen

        // ── Tab bar ──────────────────────────────────────────────────────
        TabStrip {
            id: tabStrip
            Layout.fillWidth: true
            tabModel: tabs
            targetWindow: window
            privateWindow: window.privateWindow
            onNewTabRequested: window.openNewTab(false)
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
                    leftPadding: securityButton.visible ? securitySlot.width + 8 : 8
                    rightPadding: bookmarkSlot.width > 0 ? bookmarkSlot.width + 10 : 8

                    // Text as the user typed it, before selecting a row or
                    // completing a host: Esc restores it.
                    property string typedText: ""
                    // Text before the current user edit. An edit that makes
                    // the field shorter is a deletion (Backspace/Delete) and
                    // inline completion must not refill what was just removed,
                    // even when the removed text was pasted or typed faster
                    // than the 120 ms debounce.
                    property string previousText: ""
                    // How much of previousText the user actually typed: the
                    // rest may be a selected inline completion, so replacing
                    // it counts as typing, not as a deletion.
                    property int previousTypedLength: 0
                    property bool lastEditDeleted: false

                    function syncFromTab() {
                        if (activeFocus)
                            return
                        const t = tabs.currentTab
                        // The New Tab page has no address of its own.
                        text = (t && !t.newTabPage) ? t.url.toString() : ""
                    }

                    // "kd" becomes "kde.org" with "e.org" selected, from
                    // the most visited matching history URL.
                    function completeHost() {
                        const typed = text
                        if (lastEditDeleted || typed.length < 2)
                            return
                        const host = HistoryManager.hostCompletion(typed)
                        if (host.length === 0)
                            return
                        text = host
                        previousText = host
                        previousTypedLength = typed.length
                        select(typed.length, host.length)
                    }

                    function updateSuggestions() {
                        if (!activeFocus || text.trim().length === 0) {
                            addressSuggestions.close()
                            SearchSuggestions.cancel()
                            return
                        }
                        completeHost()

                        // Rows describe what the field now shows, including an
                        // inline completion, so the Visit row appears with it.
                        const query = text.trim()
                        addressSuggestions.text = query
                        addressSuggestions.currentIndex = 0
                        addressSuggestions.open()

                        // Network suggestions are opt-in and never requested
                        // from a private tab.
                        const tab = tabs.currentTab
                        if (Settings.searchSuggestions && tab && !tab.isPrivate) {
                            SearchSuggestions.request(query)
                        } else {
                            SearchSuggestions.cancel()
                            addressSuggestions.networkSuggestions = []
                        }
                    }

                    onAccepted: {
                        const t = tabs.currentTab
                        if (!t)
                            return
                        // A query that is still pending describes the text
                        // from before the last keystroke, so its rows must not
                        // be activated. Enter then resolves the typed text,
                        // exactly as it does without a dropdown.
                        if (addressSuggestions.opened && !suggestionsTimer.running) {
                            addressSuggestions.activate(addressSuggestions.currentIndex, false)
                            return
                        }
                        suggestionsTimer.stop()
                        addressSuggestions.close()
                        t.navigateTo(ProfileManager.resolveAddress(text))
                        focus = false
                    }

                    onTextEdited: {
                        // A shrunk field is a deletion (Backspace/Delete), no
                        // matter how the removed text got there (pasted or
                        // typed before the debounce fired). Replacing the
                        // selected part of an inline completion also shrinks
                        // the text, but that is typing: it may complete again.
                        lastEditDeleted = text.length < previousText.length
                                && text.length <= previousTypedLength
                        previousText = text
                        previousTypedLength = text.length
                        typedText = text
                        // Query once the typing settles: building the rows
                        // runs the bookmark and history queries.
                        suggestionsTimer.restart()
                    }

                    Timer {
                        id: suggestionsTimer
                        interval: 120
                        onTriggered: addressBar.updateSuggestions()
                    }

                    Keys.onDownPressed: function(event) {
                        // Flush a pending query first: the open dropdown still
                        // shows the rows of the previous text.
                        if (suggestionsTimer.running) {
                            suggestionsTimer.stop()
                            addressBar.updateSuggestions()
                        }
                        if (!addressSuggestions.opened) {
                            event.accepted = false
                            return
                        }
                        addressSuggestions.currentIndex =
                            Math.min(addressSuggestions.currentIndex + 1,
                                     addressSuggestions.rows.length - 1)
                        // Show the selected row's text without querying again.
                        text = addressSuggestions.selectedText(addressSuggestions.currentIndex)
                        previousText = text
                        previousTypedLength = text.length
                        event.accepted = true
                    }

                    Keys.onUpPressed: function(event) {
                        if (suggestionsTimer.running) {
                            suggestionsTimer.stop()
                            addressBar.updateSuggestions()
                        }
                        if (!addressSuggestions.opened) {
                            event.accepted = false
                            return
                        }
                        addressSuggestions.currentIndex =
                            Math.max(addressSuggestions.currentIndex - 1, 0)
                        text = addressSuggestions.selectedText(addressSuggestions.currentIndex)
                        previousText = text
                        previousTypedLength = text.length
                        event.accepted = true
                    }

                    Keys.onEscapePressed: function(event) {
                        // A pending query would reopen the dropdown right
                        // after it was closed, so drop it even when the
                        // dropdown did not open yet (first keystroke).
                        suggestionsTimer.stop()
                        if (!addressSuggestions.opened) {
                            event.accepted = false
                            return
                        }
                        // Only the dropdown goes away; the typed text stays.
                        text = typedText
                        previousText = typedText
                        previousTypedLength = typedText.length
                        addressSuggestions.close()
                        event.accepted = true
                    }

                    // Tab and Shift+Tab never cycle the dropdown rows: they
                    // keep the field's normal focus navigation, so focus can
                    // leave the address bar as it does without a popup.

                    onActiveFocusChanged: {
                        if (activeFocus) {
                            typedText = text
                            previousText = text
                            previousTypedLength = text.length
                            lastEditDeleted = false
                            selectAll()
                        } else {
                            addressSuggestions.close()
                            SearchSuggestions.cancel()
                        }
                    }

                    Component.onCompleted: syncFromTab()

                    Row {
                        id: securitySlot
                        anchors.left: parent.left
                        anchors.leftMargin: 2
                        anchors.verticalCenter: parent.verticalCenter

                        ToolButton {
                            id: securityButton
                            readonly property string state: tabs.currentTab ? tabs.currentTab.securityState : ""

                            visible: tabs.currentTab && !tabs.currentTab.newTabPage
                                     && tabs.currentTab.url.toString().length > 0
                            display: text.length > 0 ? AbstractButton.TextBesideIcon
                                                     : AbstractButton.IconOnly
                            text: (state === "insecure" || state === "error") && !addressBar.activeFocus
                                  ? qsTr("Not Secure") : ""
                            icon.name: window.securityIconForState(state)
                            icon.color: (state === "insecure" || state === "error")
                                        ? Kirigami.Theme.negativeTextColor
                                        : Kirigami.Theme.textColor
                            flat: true
                            implicitHeight: 28
                            ToolTip.visible: hovered
                            ToolTip.text: qsTr("Site Information")
                            ToolTip.delay: 600
                            onClicked: siteInfoPopup.opened ? siteInfoPopup.close()
                                                            : siteInfoPopup.open()
                        }
                    }

                    Row {
                        id: bookmarkSlot
                        anchors.right: parent.right
                        anchors.rightMargin: 3
                        anchors.verticalCenter: parent.verticalCenter

                        ToolButton {
                            id: adBlockButton
                            readonly property string host: {
                                const text = tabs.currentTab ? tabs.currentTab.url.toString() : ""
                                const match = text.match(/^https?:\/\/([^\/?#:]+)/i)
                                return match ? match[1].toLowerCase() : ""
                            }
                            property int count: 0
                            property bool allowed: false

                            function refresh() {
                                count = AdBlockManager.blockedCount(host)
                                allowed = AdBlockManager.isAllowed(host)
                            }

                            visible: host.length > 0 && tabs.currentTab && !tabs.currentTab.newTabPage
                            display: AbstractButton.IconOnly
                            icon.name: allowed || !AdBlockManager.enabled ? "security-low"
                                                                         : "security-high"
                            icon.width: 16
                            icon.height: 16
                            flat: true
                            checked: adBlockPopup.opened
                            implicitWidth: 28
                            implicitHeight: 28
                            ToolTip.visible: hovered
                            ToolTip.text: qsTr("Ad and Tracker Blocking")
                            ToolTip.delay: 600
                            onHostChanged: refresh()
                            Component.onCompleted: refresh()
                            onClicked: adBlockPopup.opened ? adBlockPopup.close() : adBlockPopup.open()

                            Connections {
                                target: AdBlockManager
                                function onBlockedCountChanged(changedHost) {
                                    if (changedHost === adBlockButton.host)
                                        adBlockButton.refresh()
                                }
                                function onAllowListChanged() { adBlockButton.refresh() }
                            }
                            Connections {
                                target: Settings
                                function onAdBlockAllowListChanged() { adBlockButton.refresh() }
                            }

                            Rectangle {
                                visible: adBlockButton.count > 0
                                anchors { right: parent.right; top: parent.top; rightMargin: 1; topMargin: 1 }
                                width: Math.max(height, badge.implicitWidth + 6)
                                height: 13
                                radius: height / 2
                                color: Kirigami.Theme.negativeBackgroundColor
                                Label {
                                    id: badge
                                    anchors.centerIn: parent
                                    text: adBlockButton.count > 99 ? "99+" : adBlockButton.count
                                    color: Kirigami.Theme.negativeTextColor
                                    font.pixelSize: 9
                                    font.bold: true
                                }
                            }
                        }

                        ToolButton {
                            id: zoomButton
                            readonly property real factor: tabs.currentTab ? tabs.currentTab.zoomFactor : 1.0
                            visible: Math.round(factor * 100) !== 100
                            text: Math.round(factor * 100) + "%"
                            icon.name: "zoom-in"
                            icon.width: 16
                            icon.height: 16
                            display: AbstractButton.TextBesideIcon
                            flat: true
                            implicitHeight: 28
                            ToolTip.visible: hovered
                            ToolTip.text: qsTr("Reset Zoom (Ctrl+0)")
                            ToolTip.delay: 600
                            onClicked: tabs.currentTab.resetZoom()
                        }

                        ToolButton {
                            id: passwordButton
                            visible: tabs.currentTab
                                     ? tabs.currentTab.passwordUsernames.length > 0 : false
                            display: AbstractButton.IconOnly
                            icon.name: "dialog-password"
                            icon.width: 16
                            icon.height: 16
                            flat: true
                            implicitWidth: 28
                            implicitHeight: 28
                            ToolTip.visible: hovered
                            ToolTip.text: qsTr("Fill Saved Password")
                            ToolTip.delay: 600
                            onClicked: passwordMenu.popup(passwordButton, 0, passwordButton.height)

                            Menu {
                                id: passwordMenu

                                Instantiator {
                                    model: tabs.currentTab ? tabs.currentTab.passwordUsernames : []
                                    delegate: MenuItem {
                                        required property string modelData
                                        text: modelData
                                        icon.name: "user-identity"
                                        onTriggered: tabs.currentTab.fillPassword(modelData)
                                    }
                                    onObjectAdded: function(index, object) { passwordMenu.insertItem(index, object) }
                                    onObjectRemoved: function(index, object) { passwordMenu.removeItem(object) }
                                }
                            }
                        }

                        ToolButton {
                            id: readerButton
                            visible: tabs.currentTab
                                     ? (tabs.currentTab.readerAvailable || tabs.currentTab.readerActive)
                                     : false
                            display: AbstractButton.IconOnly
                            icon.name: "view-readermode"
                            icon.width: 16
                            icon.height: 16
                            flat: true
                            checked: tabs.currentTab ? tabs.currentTab.readerActive : false
                            implicitWidth: 28
                            implicitHeight: 28
                            ToolTip.visible: hovered
                            ToolTip.text: checked ? qsTr("Exit Reader Mode (Ctrl+Alt+R)")
                                                  : qsTr("Reader Mode (Ctrl+Alt+R)")
                            ToolTip.delay: 600
                            onClicked: tabs.currentTab.toggleReaderMode()
                        }

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

                        onNavigate: function(url, background) {
                            if (background) {
                                window.openUrl(url, true)
                            } else if (tabs.currentTab) {
                                tabs.currentTab.navigateTo(url)
                            }
                            addressSuggestions.close()
                            addressBar.focus = false
                        }

                        Connections {
                            target: SearchSuggestions
                            function onSuggestionsReady(text, items) {
                                // Very fast typing: drop answers for older text.
                                if (text === addressSuggestions.text)
                                    addressSuggestions.networkSuggestions = items
                            }
                        }
                    }

                    AdBlockPopup {
                        id: adBlockPopup
                        tab: tabs.currentTab
                        host: adBlockButton.host
                        x: addressBar.width - width
                        y: addressBar.height
                    }

                    SiteInfoPopup {
                        id: siteInfoPopup
                        tab: tabs.currentTab
                        x: 0
                        y: addressBar.height
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

                    MainMenu {
                        id: mainMenu
                        browserWindow: window
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

        PermissionBar {
            id: permissionBar
            tab: tabs.currentTab
            Layout.fillWidth: true
        }

        PasswordBar {
            tab: tabs.currentTab
            Layout.fillWidth: true
        }

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

    // ── Transient full-screen hint ──────────────────────────────────────
    FullScreenHint {
        id: fullScreenHint
        //: Shown for a few seconds when a page enters full screen
        text: qsTr("Press Esc to exit full screen")
        anchors.horizontalCenter: parent.horizontalCenter
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

    // ── About window (created on demand) ────────────────────────────────
    property var aboutWindow: null

    Component {
        id: aboutWindowComponent
        AboutWindow {
            tabModel: tabs
            mainWindow: window
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

    // ── Site Permissions (created on demand) ────────────────────────────
    property var sitePermissionsWindow: null

    Component {
        id: sitePermissionsComponent
        SitePermissionsDialog {}
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

    FileDialog {
        id: pdfDialog
        title: qsTr("Save as PDF")
        fileMode: FileDialog.SaveFile
        nameFilters: [qsTr("PDF (*.pdf)")]
        defaultSuffix: "pdf"
        onAccepted: if (tabs.currentTab) tabs.currentTab.printToPdf(window.localPath(selectedFile))
    }

    FileDialog {
        id: pageDialog
        title: qsTr("Save Page As")
        fileMode: FileDialog.SaveFile
        nameFilters: [qsTr("Web Page, Complete (*.html)"),
                      qsTr("Web Page, HTML Only (*.html)"),
                      qsTr("Web Archive (*.mhtml)")]
        defaultSuffix: selectedNameFilter.index === 2 ? "mhtml" : "html"
        onAccepted: {
            if (!tabs.currentTab)
                return
            const formats = [WebEngineDownloadRequest.CompleteHtmlSaveFormat,
                             WebEngineDownloadRequest.SingleHtmlSaveFormat,
                             WebEngineDownloadRequest.MimeHtmlSaveFormat]
            tabs.currentTab.savePage(window.localPath(selectedFile),
                                     formats[selectedNameFilter.index])
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

    // ── Actions ─────────────────────────────────────────────────────────
    // One per command of the main menu that has a shortcut. The menu draws the
    // shortcut from the action, and the action fires it while the menu is
    // closed, so these sequences have no separate Shortcut element.
    readonly property alias tabModel: tabs
    readonly property Action newTabAction: Action {
        text: qsTr("New Tab")
        icon.name: "tab-new"
        shortcut: "Ctrl+T"
        onTriggered: window.openNewTab(false)
    }
    readonly property Action newPrivateTabAction: Action {
        text: qsTr("New Private Tab")
        icon.name: "view-private"
        shortcut: "Ctrl+Shift+N"
        onTriggered: window.openNewTab(true)
    }
    readonly property Action newWindowAction: Action {
        text: qsTr("New Window")
        icon.name: "window-new"
        shortcut: "Ctrl+N"
        onTriggered: WindowManager.newWindow(false)
    }
    readonly property Action newPrivateWindowAction: Action {
        text: qsTr("New Private Window")
        icon.name: "view-private"
        shortcut: "Ctrl+Shift+P"
        onTriggered: WindowManager.newWindow(true)
    }
    readonly property Action historyAction: Action {
        text: qsTr("Show All History")
        icon.name: "view-history"
        shortcut: "Ctrl+H"
        onTriggered: window.openHistory()
    }
    readonly property Action reopenClosedTabAction: Action {
        text: qsTr("Reopen Closed Tab")
        icon.name: "edit-undo"
        shortcut: "Ctrl+Shift+T"
        enabled: tabs.canReopenClosedTab
        onTriggered: tabs.reopenClosedTab()
    }
    readonly property Action findAction: Action {
        text: qsTr("Find in Page…")
        icon.name: "edit-find"
        shortcut: StandardKey.Find
        enabled: tabs.currentTab ? !tabs.currentTab.newTabPage : false
        onTriggered: findBar.open()
    }
    readonly property Action printAction: Action {
        text: qsTr("Print…")
        icon.name: "document-print"
        shortcut: StandardKey.Print
        enabled: window.canPrintOrSave
        onTriggered: window.printPage()
    }
    readonly property Action savePageAction: Action {
        text: qsTr("Save Page As…")
        icon.name: "document-save-as"
        shortcut: StandardKey.Save
        enabled: window.canPrintOrSave
        onTriggered: window.savePageAs()
    }
    readonly property Action devToolsAction: Action {
        text: qsTr("Developer Tools")
        icon.name: "code-context"
        shortcut: "F12"
        enabled: tabs.currentTab ? !tabs.currentTab.newTabPage : false
        onTriggered: tabs.currentTab.toggleDevTools()
    }
    readonly property Action saveAsPdfAction: Action {
        text: qsTr("Save as PDF…")
        icon.name: "document-export"
        enabled: window.canPrintOrSave
        onTriggered: window.saveAsPdf()
    }
    readonly property Action sitePermissionsAction: Action {
        text: qsTr("Site Permissions…")
        icon.name: "security-high"
        onTriggered: window.openSitePermissions()
    }
    readonly property Action settingsAction: Action {
        //: %1 is the application name
        text: qsTr("Configure %1…").arg(Qt.application.displayName)
        icon.name: "configure"
        shortcut: "Ctrl+,"
        onTriggered: window.openSettings()
    }
    readonly property Action reportBugAction: Action {
        text: qsTr("Report a Bug…")
        icon.name: "tools-report-bug"
        onTriggered: window.openUrl("https://github.com/lukasborges/kondor/issues", true)
    }
    readonly property Action aboutAction: Action {
        //: %1 is the application name
        text: qsTr("About %1").arg(Qt.application.displayName)
        icon.name: "help-about"
        onTriggered: window.openAbout()
    }

    // ── Shortcuts ───────────────────────────────────────────────────────
    Shortcut {
        // Ctrl+Shift+, under the KDE platform theme; empty on the generic theme
        sequences: [StandardKey.Preferences]
        onActivated: window.openSettings()
    }
    Shortcut {
        sequence: "Ctrl+W"
        onActivated: window.closeTabAt(tabs.currentIndex)
    }
    Shortcut {
        sequence: "Ctrl+Shift+W"
        onActivated: window.close()
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
        sequence: "Ctrl+Alt+R"
        enabled: tabs.currentTab ? (tabs.currentTab.readerAvailable || tabs.currentTab.readerActive) : false
        onActivated: tabs.currentTab.toggleReaderMode()
    }
    Shortcut {
        sequence: "Ctrl+Shift+I"
        enabled: tabs.currentTab ? !tabs.currentTab.newTabPage : false
        onActivated: tabs.currentTab.toggleDevTools()
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
    Shortcut {
        sequences: [StandardKey.FullScreen, "F11"]
        onActivated: window.windowFullScreen = !window.windowFullScreen
    }
    // Esc only has a meaning in page full screen: the page leaves it and the
    // window follows, keeping the find bar's own Esc handling untouched.
    Shortcut {
        sequence: "Esc"
        enabled: window.pageFullScreen
        onActivated: {
            if (tabs.currentTab)
                tabs.currentTab.exitFullScreen()
        }
    }

    Connections {
        target: tabs
        function onCurrentIndexChanged() {
        }
        function onCurrentTabChanged() {
            addressSuggestions.close()
            SearchSuggestions.cancel()
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
