// #211 Tab style "Floating" (default): unified header, the active tab is a card in the toolbar color.
// Tab 3 is hovered: its close button shows. Tab 4 is loading. Tab 0 is pinned.
import QtQuick
import "common"

TabStyleFrame {
    readonly property TabStyleTabs sample: TabStyleTabs {}
    height: 260
    tabStyle: "floating"
    tabs: sample.few
    currentTab: 2
    hoveredTab: 3
}
