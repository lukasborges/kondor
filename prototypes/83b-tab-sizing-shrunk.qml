// #83 Tab sizing — more tabs than fit at 240 px: they all shrink by the same amount.
import QtQuick
import QtQuick.Controls
import "common"

BrowserFrame {
    tabs: [
        { title: "Mail", icon: "mail-message", pinned: true },
        { title: "KDE Community", icon: "kde" },
        { title: "Qt Documentation", icon: "qtcreator" },
        { title: "Planet KDE", icon: "kde" },
        { title: "LWN.net", icon: "text-html" },
        { title: "Wikipedia, the free encyclopedia", icon: "internet-web-browser" },
        { title: "Fedora Project", icon: "fedora-logo-icon" },
        { title: "ArchWiki", icon: "text-html" }
    ]
    currentTab: 2
    // (1100 − 36 pinned − 36 New Tab button) / 7 ≈ 146 px
    tabWidth: 146
    FakePage {}
}
