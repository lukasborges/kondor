// #408 Tab groups: "Work" (blue) with two tabs, "Reading" (green) collapsed to its label with a
// count, and the tab context menu adding the current tab to a group.
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "common"

TabStyleFrame {
    id: frame
    height: 460
    tabStyle: "floating"
    tabWidth: 200
    tabs: [
        { title: "Mail", icon: "internet-mail", pinned: true },
        { chip: true, title: "Work", group: "blue" },
        { title: "KDE Community", icon: "kde", group: "blue" },
        { title: "Kirigami documentation", icon: "text-html", group: "blue" },
        { chip: true, title: "Reading", group: "green", collapsed: true, count: 3 },
        { title: "Qt WebEngine overview", icon: "qtcreator" }
    ]
    currentTab: 5
    hoveredTab: 5

    Menu {
        id: tabMenu
        popupType: Popup.Item
        x: 640
        y: 40
        MenuItem { text: "New Tab"; icon.name: "tab-new" }
        MenuSeparator {}
        MenuItem { text: "Reload"; icon.name: "view-refresh" }
        MenuItem { text: "Duplicate Tab"; icon.name: "tab-duplicate" }
        MenuItem { text: "Add Tab to Group"; icon.name: "object-group"; highlighted: true; arrow: Kirigami.Icon { source: "arrow-right"; x: tabMenu.width - 28; y: 8; width: 16; height: 16 } }
        MenuItem { text: "Move Tab to New Window"; icon.name: "window-new" }
        MenuItem { text: "Pin Tab"; icon.name: "window-pin" }
        MenuItem { text: "Mute Tab"; icon.name: "audio-volume-muted" }
        MenuSeparator {}
        MenuItem { text: "Close Tab"; icon.name: "tab-close" }
        Component.onCompleted: open()
    }

    SubmenuMock {
        x: tabMenu.x + tabMenu.width - 4
        y: tabMenu.y + 76
        menuWidth: 200
        MenuItem { text: "New Group"; icon.name: "group-new" }
        MenuSeparator {}
        MenuItem { text: "Work"; icon.name: "color-fill"; icon.color: frame.groupColor("blue") }
        MenuItem { text: "Reading"; icon.name: "color-fill"; icon.color: frame.groupColor("green") }
        Component.onCompleted: open()
    }
}
