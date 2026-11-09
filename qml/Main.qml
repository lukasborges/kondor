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
        return (t && t.title.length) ? t.title + " — Kondor" : qsTr("Kondor")
    }

    TabModel {
        id: tabs
    }

    // Set once the user confirms quitting with downloads still running, so the
    // confirmation is not asked again on the retried close.
    property bool quitConfirmed: false

    onClosing: function(close) {
        if (DownloadManager.hasActiveDownloads && !window.quitConfirmed) {
            close.accepted = false
            quitDialog.open()
        }
    }

    MessageDialog {
        id: quitDialog
        title: qsTr("Quit Kondor")
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

    Component.onCompleted: {
        if (tabs.count === 0)
            tabs.addTab(false)
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
                    onClicked: tabs.addTab(false)
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

            // Double-click on the empty part of the tab bar opens a new tab.
            TapHandler {
                acceptedButtons: Qt.LeftButton
                function contains(item, sceneX, sceneY) {
                    const point = item.mapFromItem(null, sceneX, sceneY)
                    return point.x >= 0 && point.x <= item.width
                        && point.y >= 0 && point.y <= item.height
                }
                onDoubleTapped: function(eventPoint) {
                    if (contains(newTabButton, eventPoint.scenePosition.x, eventPoint.scenePosition.y))
                        return
                    if (tabBar.contentItem) {
                        const point = tabBar.contentItem.mapFromItem(null,
                                                                     eventPoint.scenePosition.x,
                                                                     eventPoint.scenePosition.y)
                        // Only the empty area after the last tab counts.
                        if (point.x <= tabBar.contentItem.contentWidth)
                            return
                    }
                    tabs.addTab(false)
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
                        if (tabs.currentTab)
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

                    function syncFromTab() {
                        if (activeFocus)
                            return
                        const t = tabs.currentTab
                        text = t ? t.url.toString() : ""
                    }

                    onAccepted: {
                        const t = tabs.currentTab
                        if (!t)
                            return
                        t.navigateTo(ProfileManager.resolveAddress(text))
                        focus = false
                    }

                    onActiveFocusChanged: {
                        if (activeFocus)
                            selectAll()
                    }

                    Component.onCompleted: syncFromTab()
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
                            onTriggered: tabs.addTab(false)
                        }
                        MenuItem {
                            text: qsTr("New Private Tab")
                            icon.name: "view-private"
                            onTriggered: tabs.addTab(true)
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
                            onTriggered: findBar.open()
                        }
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("Zoom In")
                            icon.name: "zoom-in"
                            onTriggered: {
                                if (tabs.currentTab)
                                    tabs.currentTab.zoomIn()
                            }
                        }
                        MenuItem {
                            text: qsTr("Zoom Out")
                            icon.name: "zoom-out"
                            onTriggered: {
                                if (tabs.currentTab)
                                    tabs.currentTab.zoomOut()
                            }
                        }
                        MenuItem {
                            text: qsTr("Actual Size")
                            icon.name: "zoom-original"
                            onTriggered: {
                                if (tabs.currentTab)
                                    tabs.currentTab.resetZoom()
                            }
                        }
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("History")
                            icon.name: "view-history"
                            onTriggered: window.openHistory()
                        }
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("Configure Kondor…")
                            icon.name: "configure"
                            onTriggered: window.openSettings()
                        }
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("About Kondor")
                            icon.name: "help-about"
                        }
                    }
                }
            }
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
        onActivated: tabs.addTab(false)
    }
    Shortcut {
        sequence: "Ctrl+Shift+N"
        onActivated: tabs.addTab(true)
    }
    Shortcut {
        sequence: "Ctrl+W"
        onActivated: window.closeTabAt(tabs.currentIndex)
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
        sequences: [StandardKey.Preferences, "Ctrl+,"]
        onActivated: window.openSettings()
    }
    Shortcut {
        sequences: ["F5", "Ctrl+R"]
        onActivated: {
            if (tabs.currentTab)
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
            if (tabs.currentTab)
                tabs.currentTab.zoomIn()
        }
    }
    Shortcut {
        sequences: ["Ctrl+-"]
        onActivated: {
            if (tabs.currentTab)
                tabs.currentTab.zoomOut()
        }
    }
    Shortcut {
        sequence: "Ctrl+0"
        onActivated: {
            if (tabs.currentTab)
                tabs.currentTab.resetZoom()
        }
    }
    Shortcut {
        sequences: [StandardKey.Find]
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
            addressBar.syncFromTab()
        }
    }

    Connections {
        target: tabs.currentTab
        function onUrlChanged() {
            addressBar.syncFromTab()
        }
    }
}
