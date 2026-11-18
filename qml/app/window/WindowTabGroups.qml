import QtQuick
import Kondor

Item {
    id: root

    required property TabModel tabs
    required property var browserWindow

    function openGroupEditor(group, anchor) {
        groupEditor.group = group
        groupEditor.parent = anchor
        groupEditor.x = 0
        groupEditor.y = anchor.height + 2
        groupEditor.open()
    }

    function openEditorForNewGroup(group, menu) {
        if (!group)
            return
        groupEditor.group = group
        groupEditor.parent = root
        groupEditor.x = menu.x
        groupEditor.y = menu.y
        groupEditor.open()
    }

    function moveGroupToNewWindow(group) {
        const urls = tabUrlsOf(group)
        const window = WindowManager.newWindow(browserWindow.privateWindow, urls)
        if (!window)
            return
        window.tabModel.restoreGroups([{ name: group.name, color: group.color, collapsed: group.collapsed }],
                                      urls.map(() => 0))
        closeGroup(group)
    }

    function tabUrlsOf(group) {
        const first = tabs.firstIndexOf(group)
        const urls = []
        for (let i = 0; i < tabs.tabCountOf(group); ++i)
            urls.push(tabUrl(tabs.tabAt(first + i)))
        return urls
    }

    function tabUrl(tab) {
        return tab.newTabPage ? "" : tab.url.toString()
    }

    function closeGroup(group) {
        if (tabs.tabCountOf(group) === tabs.count)
            browserWindow.close()
        else
            tabs.closeGroup(group)
    }

    TabGroupEditor {
        id: groupEditor
        tabModel: root.tabs
        onNewTabRequested: group => root.tabs.newTabInGroup(group)
        onMoveToNewWindowRequested: group => root.moveGroupToNewWindow(group)
        onCloseGroupRequested: group => root.closeGroup(group)
    }
}
