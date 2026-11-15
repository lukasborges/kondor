// #257 Sleeping tabs: "KDE Community" and "Breeze icons" are asleep (icon and title dimmed, title and
// favicon kept). The context menu of "Wikipedia" offers "Put Tab to Sleep".
import QtQuick
import QtQuick.Controls
import "common"

TabStyleFrame {
    height: 420
    tabStyle: "floating"
    tabs: [
        { title: "Mail", icon: "internet-mail", pinned: true },
        { title: "KDE Community", icon: "kde", sleeping: true },
        { title: "Plasma 6: the KDE community desktop", icon: "plasma" },
        { title: "Wikipedia, the free encyclopedia", icon: "internet-web-browser" },
        { title: "Kirigami documentation", icon: "text-html" },
        { title: "Breeze icons", icon: "preferences-desktop-icons", sleeping: true }
    ]
    currentTab: 2
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
        MenuItem { text: "Put Tab to Sleep"; icon.name: "system-suspend" }
        MenuSeparator {}
        MenuItem { text: "Close Tab"; icon.name: "tab-close" }
        MenuItem { text: "Close Other Tabs"; icon.name: "tab-close-other" }
        MenuItem { text: "Close Tabs to the Right"; icon.name: "go-last" }
        Component.onCompleted: open()
    }
}
