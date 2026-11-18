// #410 Page capture: Take Screenshot… in the page context menu (right click on the page itself).
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    FakePage {}

    Menu {
        popupType: Popup.Item
        x: 330
        y: 150
        MenuItem { text: "Back"; icon.name: "go-previous" }
        MenuItem { text: "Forward"; icon.name: "go-next"; enabled: false }
        MenuItem { text: "Reload"; icon.name: "view-refresh" }
        MenuSeparator {}
        MenuItem { text: "Save Page As…"; icon.name: "document-save" }
        MenuItem { text: "Print…"; icon.name: "document-print" }
        MenuItem { text: "Take Screenshot…"; icon.name: "select-rectangular"; highlighted: true; action: Action { shortcut: "Ctrl+Shift+S" } }
        MenuSeparator {}
        MenuItem { text: "Inspect Element"; icon.name: "code-context" }
        Component.onCompleted: open()
    }
}
