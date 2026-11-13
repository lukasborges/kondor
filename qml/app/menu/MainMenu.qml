import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Menu {
    id: root

    required property var browserWindow

    readonly property var tab: root.browserWindow.tabModel.currentTab
    readonly property bool zoomEnabled: tab ? !tab.newTabPage : false

    function toggleFullScreen() {
        root.close()
        root.browserWindow.windowFullScreen = !root.browserWindow.windowFullScreen
    }

    MenuItem { action: root.browserWindow.actions.newTabAction }
    MenuItem { action: root.browserWindow.actions.newPrivateTabAction }
    MenuItem { action: root.browserWindow.actions.newWindowAction }
    MenuItem { action: root.browserWindow.actions.newPrivateWindowAction }

    MenuSeparator {}

    BookmarkMenu {
        title: qsTr("Bookmarks")
        icon.name: "bookmarks"
        showCommands: true
        folderId: BookmarkManager.toolbarFolderId()
        onBookmarkActivated: function(url, background) {
            root.browserWindow.openUrl(url, background)
        }
        onBookmarkThisPageRequested: root.browserWindow.openBookmarkEditor()
        onManageBookmarksRequested: root.browserWindow.openBookmarks()
    }

    HistoryMenu {
        browserWindow: root.browserWindow
    }

    MenuSeparator {}

    MenuItem { action: root.browserWindow.actions.findAction }
    MenuItem { action: root.browserWindow.actions.printAction }
    MenuItem { action: root.browserWindow.actions.savePageAction }

    MenuSeparator {}

    ZoomMenuRow {
        tab: root.tab
        zoomEnabled: root.zoomEnabled
        isFullScreen: root.browserWindow.windowFullScreen
        onFullScreenToggled: root.toggleFullScreen()
    }

    MenuSeparator {}

    Menu {
        title: qsTr("More Tools")
        icon.name: "tools"

        MenuItem { action: root.browserWindow.actions.devToolsAction }
        MenuItem { action: root.browserWindow.actions.saveAsPdfAction }
        MenuItem { action: root.browserWindow.actions.sitePermissionsAction }
    }

    MenuSeparator {}

    MenuItem { action: root.browserWindow.actions.settingsAction }

    Menu {
        title: qsTr("Help")
        icon.name: "help-contents"

        MenuItem { action: root.browserWindow.actions.reportBugAction }
        MenuSeparator {}
        MenuItem { action: root.browserWindow.actions.aboutAction }
    }
}
