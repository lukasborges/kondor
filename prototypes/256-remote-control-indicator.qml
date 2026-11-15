// #256 AI agent control — toolbar indicator while remote control is on, and its popup.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    address: "https://bugs.kde.org/"
    tabs: [{ title: "KDE Bugtracking System", icon: "internet-web-browser" }]
    toolbarExtras: [
        ToolButton {
            icon.name: "automated-tasks"
            icon.color: Kirigami.Theme.neutralTextColor
            display: AbstractButton.IconOnly
            checked: true
            ToolTip.text: "Remote control is on"
            ToolTip.delay: 600
            Accessible.name: "Remote control is on"
        }
    ]
    FakePage { heading: "KDE Bugtracking System" }

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
            Button {
                Layout.alignment: Qt.AlignRight
                text: "Configure…"
                icon.name: "configure"
                flat: true
            }
        }
    }
}
