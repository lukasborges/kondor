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

    readonly property bool hasPage: tabs.currentTab ? !tabs.currentTab.newTabPage : false

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
        enabled: root.hasPage
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
    readonly property Action devToolsAction: Action {
        text: qsTr("Developer Tools")
        icon.name: "code-context"
        shortcut: "F12"
        enabled: root.hasPage
        onTriggered: root.tabs.currentTab.toggleDevTools()
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
        onTriggered: root.tabController.openUrl("https://github.com/lukasborges/kondor/issues", true)
    }
    readonly property Action aboutAction: Action {
        //: %1 is the application name
        text: qsTr("About %1").arg(Qt.application.displayName)
        icon.name: "help-about"
        onTriggered: root.dialogs.openAbout()
    }
}
