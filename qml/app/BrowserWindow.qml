import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kondor

ApplicationWindow {
    id: window
    width: 1280
    height: 820
    minimumWidth: 640
    minimumHeight: 480
    visible: true

    property bool privateWindow: false
    property var initialUrls: []
    property var initialTitles: []
    property int initialCurrentIndex: -1

    readonly property alias tabModel: tabs
    property alias windowFullScreen: fullScreenControl.windowFullScreen
    readonly property BrowserActions actions: BrowserActions {
        tabs: window.tabModel
        tabController: tabControl
        dialogs: windowDialogs
        fileDialogs: pageFileDialogs
        pageArea: pageContent
    }

    function newTabTitle(tab) {
        return tab.isPrivate ? qsTr("New Private Tab") : qsTr("New Tab")
    }

    function tabTitle(tab) {
        const application = Qt.application.displayName
        if (!tab)
            return application
        if (tab.newTabPage)
            return newTabTitle(tab) + " — " + application
        return tab.title.length ? tab.title + " — " + application : application
    }

    function windowTitle() {
        const base = tabTitle(tabs.currentTab)
        return privateWindow ? base + " — " + qsTr("Private Browsing") : base
    }

    function openUrl(url, background) { tabControl.openUrl(url, background) }
    function openUrlsInNewTabs(urls) { tabControl.openUrlsInNewTabs(urls) }
    function openSettingsPage(pageId) { windowDialogs.openSettingsPage(pageId) }
    function openBookmarks() { windowDialogs.openBookmarks() }
    function openBookmarkEditor() { toolBar.bookmarkEditor.openEditor() }
    function closeTabAt(index) { tabControl.closeTabAt(index) }
    function closeTabFor(tab) { tabControl.closeTabFor(tab) }
    function openTabContextMenu(tab, position) { tabControl.openTabContextMenu(tab, position) }

    title: windowTitle()
    onClosing: function(close) { closeGuard.handleClosing(close) }

    TabModel {
        id: tabs
        privateTabs: window.privateWindow
    }

    FullScreenController {
        id: fullScreenControl
        targetWindow: window
        tabs: window.tabModel
        hint: fullScreenHint
    }

    WindowCloseGuard {
        id: closeGuard
        tabs: window.tabModel
        browserWindow: window
    }

    WindowTabController {
        id: tabControl
        tabs: window.tabModel
        browserWindow: window
        navigationBar: toolBar
    }

    WindowDialogs {
        id: windowDialogs
        tabs: window.tabModel
        browserWindow: window
    }

    PageFileDialogs {
        id: pageFileDialogs
        tabs: window.tabModel
    }

    DownloadSaveDialog { downloadsPopup: toolBar.downloadsPopup }

    BrowserShortcuts {
        tabs: window.tabModel
        browserWindow: window
        tabController: tabControl
        dialogs: windowDialogs
        navigationBar: toolBar
        pageArea: pageContent
        fullScreen: fullScreenControl
    }

    header: ColumnLayout {
        spacing: 0
        visible: !fullScreenControl.pageFullScreen

        TabStrip {
            Layout.fillWidth: true
            tabModel: window.tabModel
            targetWindow: window
            privateWindow: window.privateWindow
            onNewTabRequested: tabControl.openNewTab(false)
        }

        NavigationToolBar {
            id: toolBar
            Layout.fillWidth: true
            tabs: window.tabModel
            browserWindow: window
        }

        BookmarksBar {
            Layout.fillWidth: true
            tabModel: window.tabModel
        }
    }

    PageArea {
        id: pageContent
        anchors.fill: parent
        tabs: window.tabModel
        browserWindow: window
    }

    FullScreenHint {
        id: fullScreenHint
        //: Shown for a few seconds when a page enters full screen
        text: qsTr("Press Esc to exit full screen")
        anchors.horizontalCenter: parent.horizontalCenter
    }
}
