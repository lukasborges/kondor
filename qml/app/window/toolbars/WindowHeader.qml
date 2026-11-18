import QtQuick
import QtQuick.Layouts
import Kondor

SlidingPane {
    id: root

    required property TabModel tabModel
    required property var browserWindow
    required property bool areToolbarsHidden
    required property bool isRevealed
    required property bool isPageFullScreen

    readonly property alias toolBar: toolBar
    readonly property alias tabSearchButton: tabStrip.searchButton

    signal newTabRequested
    signal tabSearchRequested
    signal manageBookmarksRequested

    isShown: (!areToolbarsHidden || isRevealed) && !isPageFullScreen
    takesSpace: !areToolbarsHidden && !isPageFullScreen
    contentSize: headerLayout.implicitHeight

    GridLayout {
        id: headerLayout
        width: parent.width
        columns: 1
        rowSpacing: 0

        TabStrip {
            id: tabStrip
            visible: !root.browserWindow.tabsInSideBar
            Layout.row: root.browserWindow.tabsBelowAddressBar ? 1 : 0
            Layout.fillWidth: true
            tabModel: root.tabModel
            targetWindow: root.browserWindow
            privateWindow: root.browserWindow.privateWindow
            onNewTabRequested: root.newTabRequested()
            onTabSearchRequested: root.tabSearchRequested()
        }

        NavigationToolBar {
            id: toolBar
            Layout.row: root.browserWindow.tabsBelowAddressBar ? 0 : 1
            Layout.fillWidth: true
            tabs: root.tabModel
            browserWindow: root.browserWindow
        }

        BookmarksBar {
            Layout.row: 2
            Layout.fillWidth: true
            tabModel: root.tabModel
            onManageBookmarksRequested: root.manageBookmarksRequested()
        }
    }
}
