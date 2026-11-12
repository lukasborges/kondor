import QtQuick
import Kondor

Item {
    id: root

    required property TabModel tabs
    required property var browserWindow

    property var historyWindow: null
    property var settingsWindow: null
    property var aboutWindow: null
    property var bookmarksWindow: null
    property var sitePermissionsWindow: null

    function createOnce(existing, component) {
        return existing ? existing : component.createObject(browserWindow)
    }

    function openHistory() {
        historyWindow = createOnce(historyWindow, historyWindowComponent)
        historyWindow.showWindow()
    }

    function openSettings() {
        settingsWindow = createOnce(settingsWindow, settingsWindowComponent)
        settingsWindow.showWindow()
    }

    function openExtensionsSettings() {
        openSettings()
        settingsWindow.showPage("extensions")
    }

    function openAbout() {
        aboutWindow = createOnce(aboutWindow, aboutWindowComponent)
        aboutWindow.showWindow()
    }

    function openBookmarks() {
        bookmarksWindow = createOnce(bookmarksWindow, bookmarksWindowComponent)
        bookmarksWindow.showWindow()
    }

    function openSitePermissions() {
        sitePermissionsWindow = createOnce(sitePermissionsWindow, sitePermissionsComponent)
        sitePermissionsWindow.showWindow()
    }

    Component {
        id: historyWindowComponent
        HistoryWindow { tabModel: root.tabs }
    }

    Component {
        id: settingsWindowComponent
        SettingsWindow { tabModel: root.tabs }
    }

    Component {
        id: aboutWindowComponent
        AboutWindow {
            tabModel: root.tabs
            mainWindow: root.browserWindow
        }
    }

    Component {
        id: bookmarksWindowComponent
        BookmarksWindow { tabModel: root.tabs }
    }

    Component {
        id: sitePermissionsComponent
        SitePermissionsDialog {}
    }
}
