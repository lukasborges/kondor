// New Tab page tab (#241): `go-home` instead of `tab-new`, so the tab no longer looks like the
// new tab button at the end of the strip. Tabs 1 and 2 are New Tab pages; tab 1 is the current one.
import QtQuick
import "common"

TabStyleFrame {
    height: 260
    tabStyle: "floating"
    tabs: [
        { title: "View 1 · Kondor Roadmap", icon: "text-html" },
        { title: "New Tab", icon: "go-home" },
        { title: "New Tab", icon: "go-home" }
    ]
    currentTab: 1
    hoveredTab: -1
}
