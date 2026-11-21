import QtQuick
import QtQuick.Controls
import Kondor

QtObject {
    id: root

    required property TabModel tabs
    required property var tabController
    required property var dialogs
    required property var fileDialogs
    required property var pageArea
    property Window browserWindow: null

    readonly property bool hasWindowFocus: !browserWindow || browserWindow.activeFocusItem !== null
    readonly property bool hasPage: tabs.currentTab ? !tabs.currentTab.newTabPage : false

    readonly property bool showsErrorPage: hasPage
        && (tabs.currentTab.security.certificateErrorPending
            || tabs.currentTab.security.httpsOnlyWarningPending)
    readonly property bool hasLoadedPage: hasPage
        && !["", "about:blank"].includes(String(tabs.currentTab.url))
    readonly property bool canCapture: hasPage && !tabs.currentTab.crashed
        && !showsErrorPage && hasLoadedPage

    readonly property Action newTabAction: Action {
        text: qsTr("New Tab")
        icon.name: "tab-new"
        shortcut: "Ctrl+T"
        onTriggered: root.tabController.openNewTab(false)
    }
    readonly property Action newPrivateTabAction: Action {
        text: qsTr("New Private Tab")
        icon.name: "view-private"
        shortcut: "Ctrl+Shift+N"
        enabled: ProfileManager.privateBrowsingAvailable
        onTriggered: root.tabController.openNewTab(true)
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
        enabled: ProfileManager.privateBrowsingAvailable
        onTriggered: WindowManager.newWindow(true)
    }
    readonly property Action historyAction: Action {
        text: qsTr("Show All History")
        icon.name: "view-history"
        shortcut: "Ctrl+H"
        onTriggered: root.dialogs.openHistory()
    }
    readonly property Action reopenClosedTabAction: Action {
        text: qsTr("Reopen Closed Tab")
        icon.name: "edit-undo"
        shortcut: "Ctrl+Shift+T"
        enabled: root.tabs.canReopenClosedTab
        onTriggered: root.tabs.reopenClosedTab()
    }
    readonly property Action findAction: Action {
        text: qsTr("Find in Page…")
        icon.name: "edit-find"
        shortcut: StandardKey.Find
        enabled: root.hasPage && root.hasWindowFocus
        onTriggered: root.pageArea.findBar.open()
    }
    readonly property Action printAction: Action {
        text: qsTr("Print…")
        icon.name: "document-print"
        shortcut: StandardKey.Print
        enabled: root.fileDialogs.canPrintOrSave
        onTriggered: root.fileDialogs.printPage()
    }
    readonly property Action savePageAction: Action {
        text: qsTr("Save Page As…")
        icon.name: "document-save-as"
        shortcut: StandardKey.Save
        enabled: root.fileDialogs.canPrintOrSave
        onTriggered: root.fileDialogs.savePageAs()
    }
    readonly property Action screenshotAction: Action {
        text: qsTr("Take Screenshot…")
        icon.name: "select-rectangular"
        shortcut: "Ctrl+Shift+S"
        enabled: root.canCapture
        onTriggered: root.dialogs.openScreenshot()
    }
    readonly property Action hideToolbarsAction: Action {
        text: qsTr("Hide Toolbars")
        shortcut: "Ctrl+Shift+F"
        checkable: true
        checked: Settings.hideToolbars
        onToggled: Settings.hideToolbars = checked
    }
    readonly property Action devToolsAction: Action {
        text: qsTr("Developer Tools")
        icon.name: "code-context"
        shortcut: "F12"
        enabled: root.hasPage
        onTriggered: root.tabs.currentTab.toggleDevTools()
    }
    readonly property Action responsiveModeAction: Action {
        text: qsTr("Responsive Design Mode")
        icon.name: "smartphone"
        shortcut: "Ctrl+Shift+M"
        checkable: true
        checked: root.tabs.currentTab ? root.tabs.currentTab.responsive.isActive : false
        enabled: root.tabs.currentTab !== null
        onToggled: root.tabs.currentTab.responsive.setActive(checked)
    }
    readonly property Action saveAsPdfAction: Action {
        text: qsTr("Save as PDF…")
        icon.name: "document-export"
        enabled: root.fileDialogs.canPrintOrSave
        onTriggered: root.fileDialogs.saveAsPdf()
    }
    readonly property Action sitePermissionsAction: Action {
        text: qsTr("Site Permissions…")
        icon.name: "security-high"
        onTriggered: root.dialogs.openSitePermissions()
    }
    readonly property Action settingsAction: Action {
        //: %1 is the application name
        text: qsTr("Configure %1…").arg(Qt.application.displayName)
        icon.name: "configure"
        shortcut: "Ctrl+,"
        onTriggered: root.dialogs.openSettings()
    }
    readonly property Action reportBugAction: Action {
        text: qsTr("Report a Bug…")
        icon.name: "tools-report-bug"
        onTriggered: root.tabController.openUrl("https://github.com/lukasborges/kondor-browser/issues", true)
    }
    readonly property Action aboutAction: Action {
        //: %1 is the application name
        text: qsTr("About %1").arg(Qt.application.displayName)
        icon.name: "help-about"
        onTriggered: root.dialogs.openAbout()
    }
}
