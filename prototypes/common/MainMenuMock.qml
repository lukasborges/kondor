// Main (hamburger) menu reorganized in #93: 13 rows grouped by intent.
// `openSubmenu`: "" (none), "history", "tools" or "help" shows that submenu next to it.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Item {
    id: root
    anchors.fill: parent
    property string openSubmenu: ""

    // Submenus open to the left of the main menu, level with their row.
    function placeSubmenu(submenu, title) {
        let row = null
        for (let i = 0; i < mainMenu.count; ++i) {
            const it = mainMenu.itemAt(i)
            if (it && it.text === title)
                row = it
        }
        const p = row ? row.mapToItem(root, 0, 0) : Qt.point(0, 0)
        submenu.x = mainMenu.x - submenu.menuWidth + 2
        submenu.y = p.y - submenu.topPadding
        if (row)
            row.highlighted = true
        submenu.open()
    }

    Menu {
        id: mainMenu
        popupType: Popup.Item
        closePolicy: Popup.NoAutoClose
        x: root.width - width - 8
        y: -50
        width: 300

        MenuItem { text: "New Tab"; icon.name: "tab-new"; action: Action { shortcut: "Ctrl+T" } }
        MenuItem { text: "New Private Tab"; icon.name: "view-private"; action: Action { shortcut: "Ctrl+Shift+P" } }
        MenuItem { text: "New Window"; icon.name: "window-new"; action: Action { shortcut: "Ctrl+N" } }
        MenuItem { text: "New Private Window"; icon.name: "view-private"; action: Action { shortcut: "Ctrl+Shift+N" } }
        MenuSeparator {}
        Menu { title: "Bookmarks"; icon.name: "bookmarks"; popupType: Popup.Item }
        Menu { id: historyRow; title: "History"; icon.name: "view-history"; popupType: Popup.Item }
        MenuSeparator {}
        MenuItem { text: "Find in Page…"; icon.name: "edit-find"; action: Action { shortcut: "Ctrl+F" } }
        MenuItem { text: "Print…"; icon.name: "document-print"; action: Action { shortcut: "Ctrl+P" } }
        MenuItem { text: "Save Page As…"; icon.name: "document-save-as"; action: Action { shortcut: "Ctrl+S" } }
        MenuSeparator {}
        // Zoom and full screen on one row, like Firefox and Chrome.
        Item {
            implicitWidth: mainMenu.width
            implicitHeight: zoomLayout.implicitHeight + 4
            RowLayout {
                id: zoomLayout
                anchors.fill: parent
                anchors.leftMargin: Kirigami.Units.largeSpacing + 16 + Kirigami.Units.smallSpacing * 2 + 2
                anchors.rightMargin: Kirigami.Units.smallSpacing
                spacing: 0
                Label { text: "Zoom"; Layout.fillWidth: true }
                ToolButton { icon.name: "zoom-out"; display: AbstractButton.IconOnly; flat: true }
                Label {
                    text: "100%"
                    horizontalAlignment: Text.AlignHCenter
                    Layout.preferredWidth: 48
                }
                ToolButton { icon.name: "zoom-in"; display: AbstractButton.IconOnly; flat: true }
                Kirigami.Separator { Layout.fillHeight: true; Layout.margins: 6 }
                ToolButton { icon.name: "view-fullscreen"; display: AbstractButton.IconOnly; flat: true }
            }
        }
        MenuSeparator {}
        Menu { id: toolsRow; title: "More Tools"; icon.name: "applications-development"; popupType: Popup.Item }
        MenuSeparator {}
        MenuItem { text: "Configure Kondor Browser…"; icon.name: "configure"; action: Action { shortcut: "Ctrl+," } }
        Menu { id: helpRow; title: "Help"; icon.name: "help-contents"; popupType: Popup.Item }
    }

    SubmenuMock {
        id: historyMenu
        menuWidth: 330
        MenuItem { text: "Show All History"; icon.name: "view-history"; action: Action { shortcut: "Ctrl+H" } }
        MenuItem { text: "Reopen Closed Tab"; icon.name: "edit-undo"; action: Action { shortcut: "Ctrl+Shift+T" } }
        MenuSeparator {}
        MenuItem { enabled: false; text: "Recently Closed Tabs" }
        MenuItem { text: "KDE Community"; icon.name: "kde" }
        MenuItem { text: "Qt Documentation"; icon.name: "qtcreator" }
        MenuItem { text: "LWN.net"; icon.name: "text-html" }
        MenuSeparator {}
        MenuItem { enabled: false; text: "Today" }
        MenuItem { text: "Planet KDE"; icon.name: "kde" }
        MenuItem { text: "Fedora Project"; icon.name: "fedora-logo-icon" }
        MenuItem { text: "ArchWiki"; icon.name: "text-html" }
        MenuItem { text: "Wikipedia, the free encyclopedia"; icon.name: "internet-web-browser" }
    }

    SubmenuMock {
        id: toolsMenu
        menuWidth: 280
        MenuItem { text: "Developer Tools"; icon.name: "code-context"; action: Action { shortcut: "F12" } }
        MenuItem { text: "Save as PDF…"; icon.name: "document-export" }
        MenuItem { text: "Site Permissions…"; icon.name: "security-high" }
    }

    SubmenuMock {
        id: helpMenu
        menuWidth: 250
        MenuItem { text: "Report a Bug…"; icon.name: "tools-report-bug" }
        MenuSeparator {}
        MenuItem { text: "About Kondor Browser"; icon.name: "help-about" }
    }

    // Open the submenu once the main menu has been laid out.
    Timer {
        interval: 300
        running: true
        onTriggered: {
            if (root.openSubmenu === "history") root.placeSubmenu(historyMenu, "History")
            else if (root.openSubmenu === "tools") root.placeSubmenu(toolsMenu, "More Tools")
            else if (root.openSubmenu === "help") root.placeSubmenu(helpMenu, "Help")
        }
    }

    Component.onCompleted: {
        mainMenu.open()
    }
}
