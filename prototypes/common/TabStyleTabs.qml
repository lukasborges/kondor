// Sample tabs for the #211 / #212 tab style prototypes.
import QtQuick

QtObject {
    readonly property var few: [
        { title: "Mail", icon: "internet-mail", pinned: true },
        { title: "KDE Community", icon: "kde" },
        { title: "Plasma 6: the KDE community desktop", icon: "plasma" },
        { title: "Wikipedia, the free encyclopedia", icon: "internet-web-browser" },
        { title: "Kirigami documentation", icon: "text-html", loading: true },
        { title: "Breeze icons", icon: "preferences-desktop-icons" }
    ]
    readonly property var many: few.concat([
        { title: "Dolphin file manager", icon: "system-file-manager" },
        { title: "Konsole terminal emulator", icon: "utilities-terminal" },
        { title: "Kate text editor", icon: "kate" },
        { title: "Okular document viewer", icon: "okular" },
        { title: "KDE Human Interface Guidelines", icon: "text-html" },
        { title: "Qt Quick Controls", icon: "text-html" },
        { title: "Flathub apps", icon: "internet-web-browser" },
        { title: "Plasma Mobile", icon: "plasma" },
        { title: "KDE Eco", icon: "kde" },
        { title: "Krita digital painting", icon: "krita" }
    ])
}
