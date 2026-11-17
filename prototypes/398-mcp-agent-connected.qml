// #398 Built-in MCP server — the remote control popup while an agent is connected through `kondor --mcp`.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    address: "https://kde.org/"
    tabs: [{ title: "KDE Community", icon: "internet-web-browser" }]
    toolbarExtras: [
        ToolButton {
            icon.name: "automated-tasks"
            icon.color: Kirigami.Theme.neutralTextColor
            display: AbstractButton.IconOnly
            checked: true
            ToolTip.text: "Claude Code is controlling Kondor"
            ToolTip.delay: 600
            Accessible.name: "Claude Code is controlling Kondor"
        }
    ]
    FakePage { heading: "KDE Community" }

    Popup {
        popupType: Popup.Item
        x: frame.width - width - 40
        y: -2
        width: 360
        padding: Kirigami.Units.largeSpacing
        Component.onCompleted: open()
        contentItem: ColumnLayout {
            spacing: Kirigami.Units.largeSpacing
            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Icon {
                    source: "automated-tasks"
                    color: Kirigami.Theme.neutralTextColor
                    Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                    Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                }
                ColumnLayout {
                    spacing: 0
                    Layout.fillWidth: true
                    Kirigami.Heading { level: 4; text: "Remote Control Is On" }
                    Label { text: "http://127.0.0.1:9222"; color: Kirigami.Theme.disabledTextColor }
                }
                Item { Layout.fillWidth: true }
                ToolButton {
                    icon.name: "edit-copy"
                    display: AbstractButton.IconOnly
                    ToolTip.text: "Copy Address"
                    ToolTip.delay: 600
                    Accessible.name: "Copy Address"
                }
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: "Automation tools on this computer can read and control the pages of normal windows. Private browsing is unavailable."
            }
            Kirigami.Separator { Layout.fillWidth: true }
            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Icon {
                    source: "dialog-scripts"
                    Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                    Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                }
                ColumnLayout {
                    spacing: 0
                    Layout.fillWidth: true
                    Label { text: "Claude Code"; font.bold: true }
                    Label { text: "Connected since 14:32"; color: Kirigami.Theme.disabledTextColor }
                }
                Item { Layout.fillWidth: true }
                ToolButton {
                    icon.name: "network-disconnect"
                    display: AbstractButton.IconOnly
                    ToolTip.text: "Disconnect"
                    ToolTip.delay: 600
                    Accessible.name: "Disconnect Claude Code"
                }
            }
            Kirigami.Separator { Layout.fillWidth: true }
            Button {
                Layout.alignment: Qt.AlignRight
                text: "Configure…"
                icon.name: "configure"
                flat: true
            }
        }
    }
}
