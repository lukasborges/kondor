// #211 Tab style "Floating" with 16 tabs in a private window: the tabs shrink to the minimum
// width (120) and the scroll arrows appear, as today.
import QtQuick
import "common"

TabStyleFrame {
    readonly property TabStyleTabs sample: TabStyleTabs {}
    height: 260
    tabStyle: "floating"
    tabs: sample.many
    privateWindow: true
    currentTab: 2
    tabWidth: 120
    tabScrollButtons: true
}
