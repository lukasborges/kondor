import QtQuick
import QtQuick.Controls
import Kondor

Item {
    id: root

    required property TabModel tabs
    required property var browserWindow
    required property var tabController
    required property var dialogs
    required property var navigationBar
    required property var pageArea
    required property var fullScreen

    readonly property Tab tab: tabs.currentTab
    readonly property bool hasPage: tab !== null && !tab.newTabPage
    readonly property bool canReadInReaderMode: tab !== null && (tab.readerAvailable || tab.readerActive)

    Shortcut {
        sequences: [StandardKey.Preferences]
        onActivated: root.dialogs.openSettings()
    }
    Shortcut {
        sequence: "Ctrl+W"
        onActivated: root.tabController.closeTabAt(root.tabs.currentIndex)
    }
    Shortcut {
        sequence: "Ctrl+Shift+W"
        onActivated: root.browserWindow.close()
    }
    Shortcut {
        sequences: ["Ctrl+Tab", "Ctrl+PgDown"]
        onActivated: root.tabController.stepTab(1)
    }
    Shortcut {
        sequences: ["Ctrl+Shift+Tab", "Ctrl+PgUp"]
        onActivated: root.tabController.stepTab(-1)
    }
    Shortcut {
        sequence: "Ctrl+1"
        onActivated: root.tabController.activateTabAt(0)
    }
    Shortcut {
        sequence: "Ctrl+2"
        onActivated: root.tabController.activateTabAt(1)
    }
    Shortcut {
        sequence: "Ctrl+3"
        onActivated: root.tabController.activateTabAt(2)
    }
    Shortcut {
        sequence: "Ctrl+4"
        onActivated: root.tabController.activateTabAt(3)
    }
    Shortcut {
        sequence: "Ctrl+5"
        onActivated: root.tabController.activateTabAt(4)
    }
    Shortcut {
        sequence: "Ctrl+6"
        onActivated: root.tabController.activateTabAt(5)
    }
    Shortcut {
        sequence: "Ctrl+7"
        onActivated: root.tabController.activateTabAt(6)
    }
    Shortcut {
        sequence: "Ctrl+8"
        onActivated: root.tabController.activateTabAt(7)
    }
    Shortcut {
        sequence: "Ctrl+9"
        onActivated: root.tabController.activateTabAt(root.tabs.count - 1)
    }
    Shortcut {
        sequence: "Ctrl+Shift+PgUp"
        onActivated: root.tabController.moveCurrentTab(-1)
    }
    Shortcut {
        sequence: "Ctrl+Shift+PgDown"
        onActivated: root.tabController.moveCurrentTab(1)
    }
    Shortcut {
        sequence: "Ctrl+L"
        onActivated: root.navigationBar.focusAddressBar()
    }
    Shortcut {
        sequence: "Ctrl+D"
        onActivated: root.browserWindow.openBookmarkEditor()
    }
    Shortcut {
        sequence: "Ctrl+Shift+B"
        onActivated: Settings.showBookmarksBar = !Settings.showBookmarksBar
    }
    Shortcut {
        sequence: "Ctrl+Shift+O"
        onActivated: root.browserWindow.openBookmarks()
    }
    Shortcut {
        sequences: ["F5", "Ctrl+R"]
        onActivated: if (root.hasPage) root.tab.reload()
    }
    Shortcut {
        sequences: ["Alt+Left"]
        onActivated: if (root.tab) root.tab.goBack()
    }
    Shortcut {
        sequences: ["Alt+Right"]
        onActivated: if (root.tab) root.tab.goForward()
    }
    Shortcut {
        sequences: ["Ctrl++", "Ctrl+="]
        onActivated: if (root.hasPage) root.tab.zoomIn()
    }
    Shortcut {
        sequences: ["Ctrl+-"]
        onActivated: if (root.hasPage) root.tab.zoomOut()
    }
    Shortcut {
        sequence: "Ctrl+0"
        onActivated: if (root.hasPage) root.tab.resetZoom()
    }
    Shortcut {
        sequence: "Ctrl+Alt+R"
        enabled: root.canReadInReaderMode
        onActivated: root.tab.toggleReaderMode()
    }
    Shortcut {
        sequence: "Ctrl+Shift+I"
        enabled: root.hasPage
        onActivated: root.tab.toggleDevTools()
    }
    Shortcut {
        sequence: "F3"
        enabled: root.pageArea.findBar.visible
        onActivated: root.pageArea.findBar.findNext()
    }
    Shortcut {
        sequence: "Shift+F3"
        enabled: root.pageArea.findBar.visible
        onActivated: root.pageArea.findBar.findPrevious()
    }
    Shortcut {
        sequences: [StandardKey.FullScreen, "F11"]
        onActivated: root.fullScreen.windowFullScreen = !root.fullScreen.windowFullScreen
    }
    Shortcut {
        sequence: "Esc"
        enabled: root.fullScreen.pageFullScreen
        onActivated: if (root.tab) root.tab.exitFullScreen()
    }
}
