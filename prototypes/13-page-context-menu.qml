// #13 Page context menu — right click on a link (with text selected on the page).
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    FakePage {
        paragraphs: [
            "Plasma is the desktop environment made by the KDE community. Learn more on the <a href='#'>Plasma features page</a>.",
            "With Plasma 6, the whole stack moved to Qt 6 and KDE Frameworks 6, bringing Wayland as the default session, HDR and accessibility improvements."
        ]
    }

    Menu {
        popupType: Popup.Item
        x: 330
        y: 150
        MenuItem { text: "Open Link in New Tab"; icon.name: "tab-new" }
        MenuItem { text: "Open Link in New Private Tab"; icon.name: "view-private" }
        MenuItem { text: "Open Link in New Window"; icon.name: "window-new" }
        MenuSeparator {}
        MenuItem { text: "Copy Link Address"; icon.name: "edit-copy" }
        MenuItem { text: "Save Link As…"; icon.name: "document-save" }
        MenuSeparator {}
        MenuItem { text: "Copy"; icon.name: "edit-copy" }
        MenuItem { text: "Search DuckDuckGo for “Plasma features”"; icon.name: "edit-find" }
        MenuSeparator {}
        MenuItem { text: "Inspect Element"; icon.name: "code-context" }
        Component.onCompleted: open()
    }
}
