// #376 Browser identity per site: the site information popup has "Identify as:" for this site.
// After a change the page offers Reload in an InlineBar instead of reloading by itself.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    address: "https://bank.example.com/login"
    tabs: [{ title: "Online Banking", icon: "internet-web-browser" }]
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; checked: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    belowHeader: [
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            position: Kirigami.InlineMessage.Position.Header
            visible: true
            type: Kirigami.MessageType.Information
            icon.name: "preferences-web-browser-identification"
            text: "Reload the page to use the new browser identity."
            actions: [ Kirigami.Action { text: "Reload"; icon.name: "view-refresh" } ]
        }
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
                    Kirigami.Heading { level: 4; text: "bank.example.com" }
                    Label { text: "Connection is secure"; color: Kirigami.Theme.positiveTextColor }
                }
            }
            Kirigami.Separator { Layout.fillWidth: true }
            Label { text: "Permissions for this site"; font.bold: true }
            RowLayout {
                Kirigami.Icon { source: "preferences-web-browser-identification"; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
                Label { text: "Identify as:"; Layout.fillWidth: true }
                ComboBox {
                    model: ["Kondor (default)", "Firefox", "Chrome", "Custom…"]
                    currentIndex: 1
                    Layout.preferredWidth: Kirigami.Units.gridUnit * 9
                }
            }
            Button { text: "Clear Cookies and Site Data"; icon.name: "edit-clear"; flat: true }
        }
    }
}
