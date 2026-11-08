// Target main menu with the entries added by all issues (#1 #2 #3 #4 #5 #6 #14 #16 #17).
// Order and grouping follow KDE apps (File / Edit / View / Tools).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    height: 760
    FakePage {}

    Menu {
        id: mainMenu
        popupType: Popup.Item
        x: frame.width - width - 8
        y: 0
        MenuItem { text: "New Tab"; icon.name: "tab-new"; action: Action { shortcut: "Ctrl+T" } }
        MenuItem { text: "New Window"; icon.name: "window-new"; action: Action { shortcut: "Ctrl+N" } }
        MenuItem { text: "New Private Window"; icon.name: "view-private"; action: Action { shortcut: "Ctrl+Shift+P" } }
        MenuItem { text: "Reopen Closed Tab"; icon.name: "edit-undo"; action: Action { shortcut: "Ctrl+Shift+T" } }
        MenuSeparator {}
        Menu {
            title: "Bookmarks"
            icon.name: "bookmarks"
            popupType: Popup.Item
            MenuItem { text: "Bookmark This Page"; icon.name: "bookmark-new" }
        }
        MenuItem { text: "History"; icon.name: "view-history"; action: Action { shortcut: "Ctrl+H" } }
        MenuItem { text: "Downloads"; icon.name: "download"; action: Action { shortcut: "Ctrl+Shift+Y" } }
        MenuSeparator {}
        MenuItem { text: "Find in Page…"; icon.name: "edit-find"; action: Action { shortcut: "Ctrl+F" } }
        MenuItem { text: "Save Page As…"; icon.name: "document-save-as"; action: Action { shortcut: "Ctrl+S" } }
        MenuItem { text: "Save as PDF…"; icon.name: "document-export" }
        MenuItem { text: "Print…"; icon.name: "document-print"; action: Action { shortcut: "Ctrl+P" } }
        MenuSeparator {}
        // Zoom controls on a single row, like Firefox/Falkon.
        MenuItem {
            id: zoomRow
            enabled: false
            contentItem: RowLayout {
                spacing: 0
                Label { text: "Zoom"; Layout.fillWidth: true; leftPadding: 30 }
                ToolButton { icon.name: "zoom-out"; display: AbstractButton.IconOnly }
                Label { text: "100%"; horizontalAlignment: Text.AlignHCenter; Layout.preferredWidth: 46 }
                ToolButton { icon.name: "zoom-in"; display: AbstractButton.IconOnly }
                ToolButton { icon.name: "view-fullscreen"; display: AbstractButton.IconOnly }
            }
        }
        MenuSeparator {}
        Menu {
            title: "More Tools"
            icon.name: "applications-utilities"
            popupType: Popup.Item
            MenuItem { text: "Developer Tools"; icon.name: "code-context" }
        }
        MenuItem { text: "Configure Kondor…"; icon.name: "configure"; action: Action { shortcut: "Ctrl+," } }
        MenuItem { text: "About Kondor"; icon.name: "help-about" }
        MenuSeparator {}
        MenuItem { text: "Quit"; icon.name: "application-exit"; action: Action { shortcut: "Ctrl+Q" } }
        Component.onCompleted: open()
    }
}
