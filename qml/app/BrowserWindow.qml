import QtQuick
import QtQuick.Controls
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

    property bool privateWindow: false
    property var initialUrls: []
    property var initialTitles: []
    property int initialCurrentIndex: -1

    readonly property alias tabModel: tabs
    readonly property bool tabsBelowAddressBar: Settings.tabStyle === "below"
    readonly property bool tabsInSideBar: Settings.tabStyle === "vertical"
    property alias windowFullScreen: fullScreenControl.windowFullScreen
    readonly property BrowserActions actions: BrowserActions {
        tabs: window.tabModel
        tabController: tabControl
        dialogs: windowDialogs
        fileDialogs: pageFileDialogs
        pageArea: pageContent
        browserWindow: window
    }

    function openUrl(url, background) { tabControl.openUrl(url, background) }
    function openUrlsInNewTabs(urls) { tabControl.openUrlsInNewTabs(urls) }
    function openSettingsPage(pageId) { windowDialogs.openSettingsPage(pageId) }
    function openBookmarks() { windowDialogs.openBookmarks() }
    function openNewProfile() { windowDialogs.openNewProfile() }
    function openManageProfiles() { windowDialogs.openManageProfiles() }
    function openBookmarkEditor() { toolBar.bookmarkEditor.openEditor() }
    function closeTabAt(index) { tabControl.closeTabAt(index) }
    function closeTabFor(tab) { tabControl.closeTabFor(tab) }
    function openTabContextMenu(tab, position) { tabControl.openTabContextMenu(tab, position) }

    title: windowTitle.text
    onClosing: function(close) { closeGuard.handleClosing(close) }

    WindowTitle {
        id: windowTitle
        tab: tabs.currentTab
        isPrivateWindow: window.privateWindow
    }

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

    header: GridLayout {
        columns: 1
        rowSpacing: 0
        visible: !fullScreenControl.pageFullScreen

        TabStrip {
            visible: !window.tabsInSideBar
            Layout.row: window.tabsBelowAddressBar ? 1 : 0
            Layout.fillWidth: true
            tabModel: window.tabModel
            targetWindow: window
            privateWindow: window.privateWindow
            onNewTabRequested: tabControl.openNewTab(false)
        }

        NavigationToolBar {
            id: toolBar
            Layout.row: window.tabsBelowAddressBar ? 0 : 1
            Layout.fillWidth: true
            tabs: window.tabModel
            browserWindow: window
        }

        BookmarksBar {
            Layout.row: 2
            Layout.fillWidth: true
            tabModel: window.tabModel
            onManageBookmarksRequested: window.openBookmarks()
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        LayoutMirroring.enabled: Qt.application.layoutDirection === Qt.RightToLeft
        LayoutMirroring.childrenInherit: true

        TabSideBar {
            visible: window.tabsInSideBar && !fullScreenControl.pageFullScreen
            tabModel: window.tabModel
            targetWindow: window
            Layout.fillHeight: true
            Layout.preferredWidth: implicitWidth
            onNewTabRequested: tabControl.openNewTab(false)
        }

        Kirigami.Separator {
            visible: window.tabsInSideBar && !fullScreenControl.pageFullScreen
            Layout.fillHeight: true
        }

        PageArea {
            id: pageContent
            tabs: window.tabModel
            browserWindow: window
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }

    FullScreenHint {
        id: fullScreenHint
        //: Shown for a few seconds when a page enters full screen
        text: qsTr("Press Esc to exit full screen")
        anchors.horizontalCenter: parent.horizontalCenter
    }
}
