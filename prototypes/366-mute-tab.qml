// #366 Mute tab: "Plasma 6 launch video" plays sound (speaker button), "Radio stream" is muted, the
// pinned "Mail" tab plays sound (emblem on its icon). The context menu of the video offers "Mute Tab".
import QtQuick
import QtQuick.Controls
import "common"

TabStyleFrame {
    height: 440
    tabStyle: "floating"
    tabs: [
        { title: "Mail", icon: "internet-mail", pinned: true, audio: "playing" },
        { title: "KDE Community", icon: "kde" },
        { title: "Plasma 6 launch video", icon: "plasma", audio: "playing" },
        { title: "Radio stream", icon: "internet-web-browser", audio: "muted" },
        { title: "Kirigami documentation", icon: "text-html" }
    ]
    currentTab: 2
    hoveredTab: 2

    Menu {
        popupType: Popup.Item
        x: 330
        y: 40
        MenuItem { text: "New Tab"; icon.name: "tab-new" }
        MenuSeparator {}
        MenuItem { text: "Reload"; icon.name: "view-refresh" }
        MenuItem { text: "Duplicate Tab"; icon.name: "tab-duplicate" }
        MenuItem { text: "Move Tab to New Window"; icon.name: "window-new" }
        MenuItem { text: "Pin Tab"; icon.name: "window-pin" }
        MenuItem { text: "Mute Tab"; icon.name: "audio-volume-muted" }
        MenuItem { text: "Put Tab to Sleep"; icon.name: "system-suspend" }
        MenuSeparator {}
        MenuItem { text: "Close Tab"; icon.name: "tab-close" }
        MenuItem { text: "Close Other Tabs"; icon.name: "tab-close-other" }
        MenuItem { text: "Close Tabs to the Right"; icon.name: "go-last" }
        Component.onCompleted: open()
    }
}
