// #83 Tab sizing — tabs at the 120 px minimum overflow: scroll arrows appear before the New Tab button.
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
        { title: "Phoronix", icon: "text-html" },
        { title: "Wikipedia, the free encyclopedia", icon: "internet-web-browser" },
        { title: "Fedora Project", icon: "fedora-logo-icon" },
        { title: "ArchWiki", icon: "text-html" },
        { title: "Flathub", icon: "text-html" },
        { title: "KDE Developer", icon: "kde" },
        { title: "Kondor Browser on GitHub", icon: "text-html" },
        { title: "DistroWatch", icon: "text-html" },
        { title: "freedesktop.org", icon: "text-html" }
    ]
    currentTab: 8
    tabWidth: 120
    tabScrollButtons: true
    tabScrollX: 300
    FakePage {}
}
