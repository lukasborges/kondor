// #260 Password generator — right click on a password field: Generate Password fills it at once.
import QtQuick
import QtQuick.Controls
import "common"

BrowserFrame {
    address: "https://accounts.example.org/signup"
    tabs: [{ title: "Create Account · Example", icon: "internet-web-browser" }]
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]

    SignUpPageMock { id: page }

    Menu {
        popupType: Popup.Item
        x: (parent.width - 340) / 2 + 120
        y: 200
        MenuItem { text: "Generate Password"; icon.name: "password-generate"; highlighted: true }
        MenuSeparator {}
        MenuItem { text: "Undo"; icon.name: "edit-undo"; enabled: false }
        MenuItem { text: "Redo"; icon.name: "edit-redo"; enabled: false }
        MenuSeparator {}
        MenuItem { text: "Cut"; icon.name: "edit-cut"; enabled: false }
        MenuItem { text: "Copy"; icon.name: "edit-copy"; enabled: false }
        MenuItem { text: "Paste"; icon.name: "edit-paste" }
        MenuItem { text: "Paste as Plain Text"; icon.name: "edit-paste" }
        MenuItem { text: "Select All"; icon.name: "edit-select-all"; enabled: false }
        MenuSeparator {}
        MenuItem { text: "Inspect Element"; icon.name: "code-context" }
        Component.onCompleted: open()
    }
}
