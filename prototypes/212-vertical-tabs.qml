// #212 Tab style "In a side bar": pinned tabs as icon buttons on top, the other tabs as a
// scrolling list, New Tab at the end of the list.
import QtQuick
import "common"

TabStyleFrame {
    readonly property TabStyleTabs sample: TabStyleTabs {}
    height: 560
    tabStyle: "vertical"
    tabs: sample.many
    currentTab: 2
    hoveredTab: 3
}
