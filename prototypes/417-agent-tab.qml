// #417 Agent pointer driven by kondor --mcp: the tab the agent is working on carries the
// automated-tasks icon in the remote control color (horizontal tabs), and an emblem on the
// favicon when the tab shows only its icon (pinned, collapsed side bar). Tooltip:
// "Claude Code is working in this tab".
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "common"

Column {
    spacing: 0
    TabStyleFrame {
        height: 300
        tabStyle: "floating"
        tabs: [
            { title: "Mail", icon: "internet-mail", pinned: true },
            { title: "KDE Community", icon: "kde" },
            { title: "Reforma: itens", icon: "text-html", agent: true },
            { title: "Kirigami documentation", icon: "text-html" }
        ]
        currentTab: 1
    }
    TabStyleFrame {
        height: 300
        tabStyle: "vertical"
        sideBarCollapsed: true
        tabs: [
            { title: "Mail", icon: "internet-mail", pinned: true },
            { title: "KDE Community", icon: "kde" },
            { title: "Reforma: itens", icon: "text-html", agent: true },
            { title: "Kirigami documentation", icon: "text-html" }
        ]
        currentTab: 1
    }
}
