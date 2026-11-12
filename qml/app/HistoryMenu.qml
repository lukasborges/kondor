import QtQuick
import QtQuick.Controls
import Kondor

Menu {
    id: root

    required property var browserWindow

    readonly property int staticCount: 2

    title: qsTr("History")
    icon.name: "view-history"

    onAboutToShow: root.rebuild()

    function rebuild() {
        root.removeDynamicItems()
        root.addSection(qsTr("Recently Closed Tabs"), root.closedTabEntries())
        root.addSection(qsTr("Today"), root.todayEntries())
    }

    function removeDynamicItems() {
        while (root.count > root.staticCount && root.itemAt(root.count - 1))
            root.removeItem(root.itemAt(root.count - 1))
    }

    function labelOf(title, url) {
        return title.length ? title : url.toString()
    }

    function closedTabEntries() {
        const tabs = root.browserWindow.tabModel
        return tabs.recentlyClosed.slice(0, 5).map(function(closed, index) {
            return { url: closed.url, label: root.labelOf(closed.title, closed.url),
                     activate: function() { tabs.reopenClosedTab(index) } }
        })
    }

    function todayEntries() {
        return HistoryManager.recentToday(8).map(function(visit) {
            return { url: visit.url, label: root.labelOf(visit.title, visit.url),
                     activate: function() { root.browserWindow.openUrl(visit.url, false) } }
        })
    }

    function addSection(title, entries) {
        if (!entries.length)
            return
        root.addItem(separatorComponent.createObject(null))
        root.addItem(headerComponent.createObject(null, { text: title }))
        entries.forEach(root.addEntry)
    }

    function addEntry(entry) {
        const item = siteComponent.createObject(null, { pageUrl: entry.url, label: entry.label })
        item.triggered.connect(entry.activate)
        root.addItem(item)
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
