// #211 Tab style "Classic": today's Breeze TabBar, unchanged.
import QtQuick
import "common"

BrowserFrame {
    readonly property TabStyleTabs sample: TabStyleTabs {}
    height: 260
    tabs: sample.few
    currentTab: 2
    tabWidth: 200
}
