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

    readonly property bool hasAgentMenu: RemoteControl.active && tab !== null && !tab.isPrivate

    function canPutToSleep() {
        if (!tab || tab.sleep.sleeping || tab.newTabPage || tab.crashed || tab.devToolsOpen)
            return false
        return tab !== tabModel.currentTab
    }

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
    MenuItem {
        objectName: "muteTabItem"
        text: menu.tab && menu.tab.audio.isMuted ? qsTr("Unmute Tab") : qsTr("Mute Tab")
        icon.name: menu.tab && menu.tab.audio.isMuted ? "audio-volume-high" : "audio-volume-muted"
        enabled: menu.tab !== null
        onTriggered: menu.tab.audio.toggleMuted()
    }
    MenuItem {
        objectName: "removeAgentAccessItem"
        visible: menu.hasAgentMenu && menu.tab.agent.hasAccess
        height: visible ? implicitHeight : 0
        text: qsTr("Remove Agent Access")
        icon.name: "automated-tasks"
        onTriggered: menu.tab.agent.remove()
    }
    MenuItem {
        objectName: "allowAgentAccessItem"
        visible: menu.hasAgentMenu && !menu.tab.agent.hasAccess
        height: visible ? implicitHeight : 0
        text: qsTr("Allow Agent Access")
        icon.name: "automated-tasks"
        onTriggered: menu.tab.agent.allow()
    }
    MenuItem {
        objectName: "putToSleepItem"
        text: qsTr("Put Tab to Sleep")
        icon.name: "system-suspend"
        enabled: menu.canPutToSleep()
        onTriggered: menu.tab.sleep.putToSleep()
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
