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
    property var initialProfile: null
    property var initialRequest: null

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

    function showToolbars() {
        if (windowFullScreen)
            windowFullScreen = false
        else
            Settings.hideToolbars = false
        toolbarsHint.hide()
    }
    function revealToolbars() { toolbarVisibility.reveal() }
    function openUrl(url, background) { tabControl.openUrl(url, background) }
    function openUrlInNewTab(url) { tabControl.openUrlInNewTab(url) }
    function openUrlsInNewTabs(urls) { tabControl.openUrlsInNewTabs(urls) }
    function openSettingsPage(pageId) { windowDialogs.openSettingsPage(pageId) }
    function openBookmarks() { windowDialogs.openBookmarks() }
    function openNewProfile() { windowDialogs.openNewProfile() }
    function openManageProfiles() { windowDialogs.openManageProfiles() }
    function openBookmarkEditor() { headerPane.toolBar.bookmarkEditor.openEditor() }
    function closeTabAt(index) { tabControl.closeTabAt(index) }
    function closeTabFor(tab) { tabControl.closeTabFor(tab) }
    function openTabContextMenu(tab, position) { tabControl.openTabContextMenu(tab, position) }

    title: windowTitle.text
    onClosing: function(close) { closeGuard.handleClosing(close) }

    RealInputWatch {
        window: window
        active: RemoteControl.active
    }

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
        navigationBar: headerPane.toolBar
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

    DownloadSaveDialog { downloadsPopup: headerPane.toolBar.downloadsPopup }

    BrowserShortcuts {
        tabs: window.tabModel
        browserWindow: window
        tabController: tabControl
        dialogs: windowDialogs
        navigationBar: headerPane.toolBar
        pageArea: pageContent
        fullScreen: fullScreenControl
    }

    header: WindowHeader {
        id: headerPane
        tabModel: window.tabModel
        browserWindow: window
        areToolbarsHidden: toolbarVisibility.areHidden
        isRevealed: toolbarVisibility.isRevealed
        isPageFullScreen: fullScreenControl.pageFullScreen
        onNewTabRequested: tabControl.openNewTab(false)
        onManageBookmarksRequested: window.openBookmarks()
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        LayoutMirroring.enabled: Qt.application.layoutDirection === Qt.RightToLeft
        LayoutMirroring.childrenInherit: true

        WindowSideBar {
            id: sideBarPane
            visible: window.tabsInSideBar && !fullScreenControl.pageFullScreen
            tabModel: window.tabModel
            targetWindow: window
            areToolbarsHidden: toolbarVisibility.areHidden
            isRevealed: toolbarVisibility.isRevealed
            onNewTabRequested: tabControl.openNewTab(false)
        }

        PageArea {
            id: pageContent
            tabs: window.tabModel
            browserWindow: window
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }

    EdgeTrigger {
        id: topEdgeTrigger
        enabled: toolbarVisibility.areHidden && !toolbarVisibility.isRevealed
        width: parent.width
        height: 4
    }

    EdgeTrigger {
        id: leftEdgeTrigger
        enabled: toolbarVisibility.areHidden && !toolbarVisibility.isRevealed && window.tabsInSideBar
        width: 4
        height: parent.height
    }

    ToolbarVisibility {
        id: toolbarVisibility
        targetWindow: window
        panes: [headerPane, sideBarPane]
        isPointerAtEdge: topEdgeTrigger.isHovered || leftEdgeTrigger.isHovered
        isWindowFullScreen: fullScreenControl.windowFullScreen
        isPageFullScreen: fullScreenControl.pageFullScreen
        onHiddenHintRequested: toolbarsHint.show()
        onHiddenHintCancelled: toolbarsHint.hide()
    }

    FullScreenHint {
        id: fullScreenHint
        //: Shown for a few seconds when a page enters full screen
        text: qsTr("Press Esc to exit full screen")
        anchors.horizontalCenter: parent.horizontalCenter
    }

    ToolbarsHiddenHint {
        id: toolbarsHint
        isWindowFullScreen: window.windowFullScreen
        anchors.horizontalCenter: parent.horizontalCenter
        onActionTriggered: window.showToolbars()
    }
}
