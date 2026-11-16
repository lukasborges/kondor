// #260 Password generator — The row hovered, with its tooltip.
import QtQuick
import QtQuick.Controls
import "common"

BrowserFrame {
    id: frame
    address: "https://accounts.example.org/signup"
    tabs: [{ title: "Create Account · Example", icon: "internet-web-browser" }]
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]

    SignUpPageMock { id: page }

    SuggestedPasswordPopupMock {
        rowHighlighted: true
        x: (parent.width - 340) / 2
        y: 216
        width: 340
    }
}
