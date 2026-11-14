// #211 Tab style "Below the address bar": the tabs sit under the navigation toolbar and the active
// tab uses the Breeze selection colors.
import QtQuick
import "common"

TabStyleFrame {
    readonly property TabStyleTabs sample: TabStyleTabs {}
    height: 260
    tabStyle: "below"
    tabs: sample.few
    currentTab: 2
    hoveredTab: 3
}
