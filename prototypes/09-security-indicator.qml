// #9 Security indicator — padlock in the address bar and site information popup.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
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
                    Kirigami.Heading { level: 4; text: "kde.org" }
                    Label { text: "Connection is secure"; color: Kirigami.Theme.positiveTextColor }
                }
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: Kirigami.Theme.disabledTextColor
                text: "Certificate issued by Let's Encrypt (R11), valid until Feb 12, 2027."
            }
            Kirigami.Separator { Layout.fillWidth: true }
            Label { text: "Permissions for this site"; font.bold: true }
            RowLayout {
                Kirigami.Icon { source: "preferences-desktop-notification"; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
                Label { text: "Notifications"; Layout.fillWidth: true }
                Label { text: "Allowed"; color: Kirigami.Theme.positiveTextColor }
                ToolButton { icon.name: "edit-undo"; display: AbstractButton.IconOnly }
            }
            Button { text: "Clear Cookies and Site Data"; icon.name: "edit-clear"; flat: true }
        }
    }
}
