import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// The main (hamburger) menu: rows grouped by intent. Every command with a
// shortcut is an Action declared by the BrowserWindow (the Breeze style draws
// a shortcut only from MenuItem.action), so the shortcut also works while the
// menu is closed.
Menu {
    id: root

    // The BrowserWindow that owns the menu and its actions.
    required property var browserWindow

    readonly property var tab: root.browserWindow.tabModel.currentTab
    readonly property bool zoomEnabled: tab ? !tab.newTabPage : false

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

    Menu {
        id: historyMenu

        // The static items below; everything after them is rebuilt.
        readonly property int staticCount: 2

        title: qsTr("History")
        icon.name: "view-history"

        onAboutToShow: rebuild()

        function rebuild() {
            while (count > staticCount) {
                const item = itemAt(count - 1)
                if (!item)
                    break
                removeItem(item)
            }

            const closed = root.browserWindow.tabModel.recentlyClosed.slice(0, 5)
            if (closed.length) {
                addItem(separatorComponent.createObject(null))
                addItem(headerComponent.createObject(null, { text: qsTr("Recently Closed Tabs") }))
                for (let i = 0; i < closed.length; ++i) {
                    const index = i
                    const item = siteComponent.createObject(null, {
                        pageUrl: closed[i].url,
                        label: closed[i].title.length ? closed[i].title : closed[i].url.toString()
                    })
                    item.triggered.connect(function() {
                        root.browserWindow.tabModel.reopenClosedTab(index)
                    })
                    addItem(item)
                }
            }

            const today = HistoryManager.recentToday(8)
            if (today.length) {
                addItem(separatorComponent.createObject(null))
                addItem(headerComponent.createObject(null, { text: qsTr("Today") }))
                for (let j = 0; j < today.length; ++j) {
                    const url = today[j].url
                    const item = siteComponent.createObject(null, {
                        pageUrl: url,
                        label: today[j].title.length ? today[j].title : url
                    })
                    item.triggered.connect(function() {
                        root.browserWindow.openUrl(url, false)
                    })
                    addItem(item)
                }
            }
        }

        MenuItem { action: root.browserWindow.actions.historyAction }
        MenuItem { action: root.browserWindow.actions.reopenClosedTabAction }

        Component {
            id: separatorComponent
            MenuSeparator {}
        }
        Component {
            id: headerComponent
            MenuItem {
                enabled: false
            }
        }
        Component {
            id: siteComponent
            SiteMenuItem {}
        }
    }

    MenuSeparator {}

    MenuItem { action: root.browserWindow.actions.findAction }
    MenuItem { action: root.browserWindow.actions.printAction }
    MenuItem { action: root.browserWindow.actions.savePageAction }

    MenuSeparator {}

    // Zoom and full screen on one row, like Firefox and Chrome. The buttons
    // do not close the menu, so the user can click them repeatedly.
    Item {
        implicitWidth: zoomLayout.implicitWidth
        implicitHeight: zoomLayout.implicitHeight + 4

        RowLayout {
            id: zoomLayout
            anchors.fill: parent
            anchors.leftMargin: Kirigami.Units.largeSpacing + Kirigami.Units.iconSizes.small
                                + Kirigami.Units.smallSpacing * 2 + 2
            anchors.rightMargin: Kirigami.Units.smallSpacing
            spacing: 0

            Label {
                text: qsTr("Zoom")
                Layout.fillWidth: true
            }
            ToolButton {
                icon.name: "zoom-out"
                display: AbstractButton.IconOnly
                flat: true
                enabled: root.zoomEnabled
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Zoom Out (Ctrl+−)")
                ToolTip.delay: 600
                onClicked: root.tab.zoomOut()
            }
            ToolButton {
                Layout.preferredWidth: Kirigami.Units.gridUnit * 3
                flat: true
                enabled: root.zoomEnabled
                text: (root.tab ? Math.round(root.tab.zoomFactor * 100) : 100) + "%"
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Reset Zoom (Ctrl+0)")
                ToolTip.delay: 600
                onClicked: root.tab.resetZoom()
            }
            ToolButton {
                icon.name: "zoom-in"
                display: AbstractButton.IconOnly
                flat: true
                enabled: root.zoomEnabled
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Zoom In (Ctrl++)")
                ToolTip.delay: 600
                onClicked: root.tab.zoomIn()
            }
            Kirigami.Separator {
                Layout.fillHeight: true
                Layout.margins: 6
            }
            ToolButton {
                icon.name: root.browserWindow.windowFullScreen ? "view-restore" : "view-fullscreen"
                display: AbstractButton.IconOnly
                flat: true
                ToolTip.visible: hovered
                ToolTip.text: root.browserWindow.windowFullScreen ? qsTr("Exit Full Screen (F11)")
                                                           : qsTr("Full Screen (F11)")
                ToolTip.delay: 600
                onClicked: {
                    root.close()
                    root.browserWindow.windowFullScreen = !root.browserWindow.windowFullScreen
                }
            }
        }
    }

    MenuSeparator {}

    Menu {
        title: qsTr("More Tools")
        icon.name: "applications-development"

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
