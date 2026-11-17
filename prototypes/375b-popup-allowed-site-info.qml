// #375 The site information popup lists the pop-up exception with the other site permissions, and
// Revoke removes it (the Site Permissions dialog lists it the same way).
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
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; checked: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    FakePage {}

    Popup {
        popupType: Popup.Item
        x: 166
        y: -4
        width: 360
        padding: Kirigami.Units.largeSpacing
        Component.onCompleted: open()
        contentItem: ColumnLayout {
            spacing: Kirigami.Units.largeSpacing
            RowLayout {
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Icon { source: "security-high"; Layout.preferredWidth: 32; Layout.preferredHeight: 32 }
                ColumnLayout {
                    spacing: 0
                    Kirigami.Heading { level: 4; text: "tickets.example.com" }
                    Label { text: "Connection is secure"; color: Kirigami.Theme.positiveTextColor }
                }
            }
            Kirigami.Separator { Layout.fillWidth: true }
            Label { text: "Permissions for this site"; font.bold: true }
            RowLayout {
                Kirigami.Icon { source: "window-duplicate-symbolic"; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
                Label { text: "Pop-ups"; Layout.fillWidth: true }
                Label { text: "Allowed"; color: Kirigami.Theme.positiveTextColor }
                ToolButton { icon.name: "edit-undo"; display: AbstractButton.IconOnly }
            }
            RowLayout {
                Kirigami.Icon { source: "preferences-desktop-notification"; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
                Label { text: "Notifications"; Layout.fillWidth: true }
                Label { text: "Blocked"; color: Kirigami.Theme.negativeTextColor }
                ToolButton { icon.name: "edit-undo"; display: AbstractButton.IconOnly }
            }
            Button { text: "Clear Cookies and Site Data"; icon.name: "edit-clear"; flat: true }
        }
    }
}
