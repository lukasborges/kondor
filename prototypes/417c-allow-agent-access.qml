// #417 Agent tabs: the tab context menu of a user's own tab offers "Allow Agent Access", which
// hands the tab to agents: it gets the mark and kondor --mcp sessions may use it. An agent's tab
// offers "Remove Agent Access" instead (417b).
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
    hoveredTab: 3

    Menu {
        popupType: Popup.Item
        x: 560
        y: 40
        MenuItem { text: "New Tab"; icon.name: "tab-new" }
        MenuSeparator {}
        MenuItem { text: "Reload"; icon.name: "view-refresh" }
        MenuItem { text: "Duplicate Tab"; icon.name: "tab-duplicate" }
        MenuItem { text: "Move Tab to New Window"; icon.name: "window-new" }
        MenuItem { text: "Pin Tab"; icon.name: "window-pin" }
        MenuItem { text: "Mute Tab"; icon.name: "audio-volume-muted" }
        MenuItem { text: "Allow Agent Access"; icon.name: "automated-tasks"; highlighted: true }
        MenuSeparator {}
        MenuItem { text: "Close Tab"; icon.name: "tab-close" }
        Component.onCompleted: open()
    }
}
