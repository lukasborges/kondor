// #366 Mute tab in the side bar: the muted tab offers "Unmute Tab".
import QtQuick
import QtQuick.Controls
import "common"

TabStyleFrame {
    height: 520
    tabStyle: "vertical"
    tabs: [
        { title: "Mail", icon: "internet-mail", pinned: true, audio: "playing" },
        { title: "KDE Community", icon: "kde" },
        { title: "Plasma 6 launch video", icon: "plasma", audio: "playing" },
        { title: "Radio stream", icon: "internet-web-browser", audio: "muted" },
        { title: "Kirigami documentation", icon: "text-html" }
    ]
    currentTab: 2
    hoveredTab: 3

    Menu {
        popupType: Popup.Item
        x: 200
        y: 196
        MenuItem { text: "New Tab"; icon.name: "tab-new" }
        MenuSeparator {}
        MenuItem { text: "Reload"; icon.name: "view-refresh" }
        MenuItem { text: "Duplicate Tab"; icon.name: "tab-duplicate" }
        MenuItem { text: "Move Tab to New Window"; icon.name: "window-new" }
        MenuItem { text: "Pin Tab"; icon.name: "window-pin" }
        MenuItem { text: "Unmute Tab"; icon.name: "audio-volume-high" }
        MenuItem { text: "Put Tab to Sleep"; icon.name: "system-suspend" }
        MenuSeparator {}
        MenuItem { text: "Close Tab"; icon.name: "tab-close" }
        MenuItem { text: "Close Other Tabs"; icon.name: "tab-close-other" }
        MenuItem { text: "Close Tabs to the Right"; icon.name: "go-last" }
        Component.onCompleted: open()
    }
}
