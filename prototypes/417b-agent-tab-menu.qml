// #417 Agent tabs: the tab context menu of an agent's tab offers "Remove Agent Access", which
// takes the tab back from every agent session (the mark goes; the tab stays). A user's own tab
// offers "Allow Agent Access" instead (not shown here).
import QtQuick
import QtQuick.Controls
import "common"

TabStyleFrame {
    height: 460
    tabStyle: "floating"
    tabs: [
        { title: "Mail", icon: "internet-mail", pinned: true },
        { title: "KDE Community", icon: "kde" },
        { title: "Reforma: itens", icon: "text-html", agent: true },
        { title: "Kirigami documentation", icon: "text-html" }
    ]
    currentTab: 1
    hoveredTab: 2

    Menu {
        popupType: Popup.Item
        x: 330
        y: 40
        MenuItem { text: "New Tab"; icon.name: "tab-new" }
        MenuSeparator {}
        MenuItem { text: "Reload"; icon.name: "view-refresh" }
        MenuItem { text: "Duplicate Tab"; icon.name: "tab-duplicate" }
        MenuItem { text: "Move Tab to New Window"; icon.name: "window-new" }
        MenuItem { text: "Pin Tab"; icon.name: "window-pin" }
        MenuItem { text: "Mute Tab"; icon.name: "audio-volume-muted" }
        MenuItem { text: "Remove Agent Access"; icon.name: "automated-tasks"; highlighted: true }
        MenuSeparator {}
        MenuItem { text: "Close Tab"; icon.name: "tab-close" }
        Component.onCompleted: open()
    }
}
