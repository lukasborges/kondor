// #83 Tab sizing — a few tabs: every unpinned tab is 240 px wide, whatever its title.
import QtQuick
import QtQuick.Controls
import "common"

BrowserFrame {
    tabs: [
        { title: "Mail", icon: "mail-message" },
        { title: "KDE Community - Powerful, multi-platform, and for everyone", icon: "kde" },
        { title: "Qt Documentation", icon: "qtcreator" }
    ]
    currentTab: 1
    tabWidth: 240
    FakePage {}
}
