STUB_WINDOW_QML = """
import QtQuick
import QtQuick.Controls
import Kondor

ApplicationWindow {
    id: window
    width: 600
    height: 400
    visible: true

    property alias tabModel: tabs
    property int newTabs: 0
    property int reopens: 0
    property var openedUrls: []
    property bool windowFullScreen: false
    function openUrl(url, background) { openedUrls.push(url.toString()) }
    function openBookmarkEditor() {}
    function openBookmarks() {}

    TabModel { id: tabs }

    readonly property QtObject actions: QtObject {
        readonly property Action newTabAction: Action {
            text: "New Tab"
            shortcut: "Ctrl+T"
            onTriggered: window.newTabs++
        }
        readonly property Action newPrivateTabAction: Action {
            text: "New Private Tab"
            shortcut: "Ctrl+Shift+N"
        }
        readonly property Action newWindowAction: Action { text: "New Window"; shortcut: "Ctrl+N" }
        readonly property Action newPrivateWindowAction: Action {
            text: "New Private Window"
            shortcut: "Ctrl+Shift+P"
        }
        readonly property Action historyAction: Action {
            text: "Show All History"
            shortcut: "Ctrl+H"
        }
        readonly property Action reopenClosedTabAction: Action {
            text: "Reopen Closed Tab"; shortcut: "Ctrl+Shift+T"; enabled: tabs.canReopenClosedTab
            onTriggered: { tabs.reopenClosedTab(); window.reopens++ }
        }
        readonly property Action findAction: Action {
            text: "Find in Page…"
            shortcut: StandardKey.Find
        }
        readonly property Action printAction: Action { text: "Print…"; shortcut: StandardKey.Print }
        readonly property Action savePageAction: Action {
            text: "Save Page As…"
            shortcut: StandardKey.Save
        }
        readonly property Action hideToolbarsAction: Action {
            text: "Hide Toolbars"
            shortcut: "Ctrl+Shift+F"
            checkable: true
        }
        readonly property Action devToolsAction: Action { text: "Developer Tools"; shortcut: "F12" }
        readonly property Action saveAsPdfAction: Action { text: "Save as PDF…" }
        readonly property Action sitePermissionsAction: Action { text: "Site Permissions…" }
        readonly property Action settingsAction: Action {
            text: "Configure Kondor Browser…"
            shortcut: "Ctrl+,"
        }
        readonly property Action reportBugAction: Action { text: "Report a Bug…" }
        readonly property Action aboutAction: Action { text: "About Kondor Browser" }
    }

    MainMenu {
        id: mainMenu
        browserWindow: window
    }
}
"""

MAIN_MENU_QML = "MainMenu {\n        id: mainMenu\n        browserWindow: window\n    }"
TOOL_BAR_QML = (
    "function openSettingsPage(pageId) {}\n"
    "    function revealToolbars() {}\n"
    "    NavigationToolBar { tabs: tabs; browserWindow: window; width: 600 }"
)
TOOL_BAR_WINDOW_QML = STUB_WINDOW_QML.replace(MAIN_MENU_QML, TOOL_BAR_QML)
