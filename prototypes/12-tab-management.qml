// #12 Tab management — favicons, loading tab, pinned tabs, private tab and tab context menu.
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    tabs: [
        { title: "Mail", icon: "mail-message", pinned: true },
        { title: "Calendar", icon: "view-calendar", pinned: true },
        { title: "KDE Community", icon: "kde" },
        { title: "Loading…", icon: "text-html", loading: true },
        { title: "Private Browsing", private: true },
        { title: "Qt Documentation", icon: "qtcreator" }
    ]
    currentTab: 2
    FakePage {}

    Menu {
        popupType: Popup.Item
        x: 300
        y: -50
        MenuItem { text: "New Tab"; icon.name: "tab-new" }
        MenuSeparator {}
        MenuItem { text: "Reload"; icon.name: "view-refresh" }
        MenuItem { text: "Duplicate Tab"; icon.name: "tab-duplicate" }
        MenuItem { text: "Pin Tab"; icon.name: "window-pin" }
        MenuItem { text: "Move to New Window"; icon.name: "window-new" }
        MenuSeparator {}
        MenuItem { text: "Close Tab"; icon.name: "tab-close" }
        MenuItem { text: "Close Other Tabs"; icon.name: "tab-close-other" }
        MenuItem { text: "Close Tabs to the Right"; icon.name: "go-last" }
        MenuSeparator {}
        MenuItem { text: "Reopen Closed Tab"; icon.name: "edit-undo" }
        Component.onCompleted: open()
    }
}
