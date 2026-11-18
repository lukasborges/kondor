// #408 Tab groups in the side bar: a header row per group (color dot, name, arrow); its tabs are
// indented with a bar of the group's color. "Reading" is collapsed and shows its tab count.
import QtQuick
import "common"

TabStyleFrame {
    height: 520
    tabStyle: "vertical"
    tabs: [
        { title: "Mail", icon: "internet-mail", pinned: true },
        { chip: true, title: "Work", group: "blue" },
        { title: "KDE Community", icon: "kde", group: "blue" },
        { title: "Kirigami documentation", icon: "text-html", group: "blue" },
        { chip: true, title: "Reading", group: "green", collapsed: true, count: 3 },
        { title: "Qt WebEngine overview", icon: "qtcreator" },
        { title: "Planet KDE", icon: "internet-web-browser" }
    ]
    currentTab: 3
}
