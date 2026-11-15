// #242 Side Bar tab style, collapsed: icons only. Pinned tabs on top, the current tab highlighted,
// the hovered tab shows its title in a tooltip, New Tab and the expand button at the bottom.
import QtQuick
import "common"

TabStyleFrame {
    readonly property TabStyleTabs sample: TabStyleTabs {}
    height: 560
    tabStyle: "vertical"
    sideBarCollapsed: true
    tabs: sample.many
    currentTab: 2
    hoveredTab: 4
}
