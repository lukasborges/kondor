import QtQuick
import QtQuick.Controls
import Kondor

Menu {
    id: menu

    property Tab tab: null
    property int tabIndex: -1
    property TabModel tabModel: null
    property var targetWindow: null

    signal newTabRequested()
    signal moveToNewWindowRequested()

    MenuItem {
        text: qsTr("New Tab")
        icon.name: "tab-new"
        onTriggered: menu.newTabRequested()
    }
    MenuSeparator {}
    MenuItem {
        text: qsTr("Reload")
        icon.name: "view-refresh"
        enabled: menu.tab !== null
        onTriggered: {
            if (menu.tab)
                menu.tab.reload()
        }
    }
    MenuItem {
        text: qsTr("Duplicate Tab")
        icon.name: "tab-duplicate"
        enabled: menu.tab !== null
        onTriggered: menu.tabModel.duplicateTab(menu.tabIndex)
    }
    MenuItem {
        text: qsTr("Move Tab to New Window")
        icon.name: "window-new"
        enabled: menu.tab !== null
        onTriggered: menu.moveToNewWindowRequested()
    }
    MenuItem {
        text: menu.tab && menu.tab.pinned ? qsTr("Unpin Tab") : qsTr("Pin Tab")
        icon.name: "window-pin"
        enabled: menu.tab !== null
        onTriggered: menu.tabModel.setPinned(menu.tabIndex, !menu.tab.pinned)
    }
    MenuSeparator {}
    MenuItem {
        text: qsTr("Close Tab")
        icon.name: "tab-close"
        enabled: menu.tab !== null
        onTriggered: menu.targetWindow.closeTabAt(menu.tabIndex)
    }
    MenuItem {
        text: qsTr("Close Other Tabs")
        icon.name: "tab-close-other"
        enabled: menu.tab !== null
        onTriggered: menu.tabModel.closeOtherTabs(menu.tabIndex)
    }
    MenuItem {
        text: qsTr("Close Tabs to the Right")
        icon.name: "go-last"
        enabled: menu.tab !== null && menu.tabIndex < menu.tabModel.count - 1
        onTriggered: menu.tabModel.closeTabsToTheRight(menu.tabIndex)
    }
}
