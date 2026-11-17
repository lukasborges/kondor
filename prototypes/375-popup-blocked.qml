// #375 Pop-up blocker: the page tried to open two pop-ups without a click. The address bar shows the
// blocked pop-ups button; its panel lists them (a click opens one) and allows the site from now on.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    address: "https://tickets.example.com/checkout"
    tabs: [{ title: "Checkout - Tickets", icon: "internet-web-browser" }]
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    addressRight: [
        ToolButton { icon.name: "window-duplicate-symbolic"; icon.width: 16; icon.height: 16; display: AbstractButton.IconOnly; flat: true; checked: true; implicitWidth: 28; implicitHeight: 28 },
        ToolButton { icon.name: "non-starred-symbolic"; icon.width: 16; icon.height: 16; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    FakePage {}

    Popup {
        popupType: Popup.Item
        x: frame.width - width - 96
        y: -4
        width: 340
        padding: Kirigami.Units.largeSpacing
        Component.onCompleted: open()
        contentItem: ColumnLayout {
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Heading { level: 4; text: "Blocked Pop-ups" }
            ItemDelegate {
                Layout.fillWidth: true
                icon.name: "window-new"
                text: "payment.example.net/3ds?session=81f2…"
                highlighted: true
            }
            ItemDelegate {
                Layout.fillWidth: true
                icon.name: "window-new"
                text: "tickets.example.com/seat-map"
            }
            Kirigami.Separator { Layout.fillWidth: true }
            Switch {
                Layout.fillWidth: true
                text: "Allow pop-ups from tickets.example.com"
            }
        }
    }
}
