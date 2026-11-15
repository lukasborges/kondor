// #257 Sleeping tabs in the side bar (#212): sleeping rows keep their favicon and title, dimmed.
// The pinned "Calendar" tab was put to sleep from its context menu.
import QtQuick
import "common"

TabStyleFrame {
    readonly property TabStyleTabs sample: TabStyleTabs {}
    height: 560
    tabStyle: "vertical"
    tabs: [
        { title: "Mail", icon: "internet-mail", pinned: true },
        { title: "Calendar", icon: "view-calendar", pinned: true, sleeping: true }
    ].concat(sample.many.slice(1).map((tab, index) =>
        Object.assign({}, tab, { loading: false, sleeping: [0, 3, 5, 6, 7, 9, 11, 13].includes(index) })))
    currentTab: 3
    hoveredTab: 4
}
