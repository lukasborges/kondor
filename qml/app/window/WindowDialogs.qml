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

    ImportNotifier {}

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

    function openSettingsPage(pageId) {
        openSettings()
        settingsWindow.showPage(pageId)
    }

    function openAbout() {
        aboutWindow = createOnce(aboutWindow, aboutWindowComponent)
        aboutWindow.showWindow()
    }

    function openBookmarks() {
        bookmarksWindow = createOnce(bookmarksWindow, bookmarksWindowComponent)
        bookmarksWindow.showWindow()
    }

    function openNewProfile() {
        newProfileDialog.openForNew()
    }

    function openManageProfiles() {
        if (!UserProfiles.manageWindow)
            UserProfiles.manageWindow = manageProfilesComponent.createObject(browserWindow)
        UserProfiles.manageWindow.showWindow()
    }

    function openSitePermissions() {
        sitePermissionsWindow = createOnce(sitePermissionsWindow, sitePermissionsComponent)
        sitePermissionsWindow.showWindow()
    }

    ProfileDialog {
        id: newProfileDialog
        onProfileSaved: function(profileId, isNew) {
            if (isNew)
                UserProfiles.openWindow(profileId)
        }
    }

    Component {
        id: manageProfilesComponent
        ManageProfilesWindow {}
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
