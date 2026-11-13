// #176 Saved logins panel: click an account to fill, or copy its user name or password.
// Feedback follows the KDE HIG: the copy button turns into a check mark for 2 s, no message.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    address: "https://accounts.example.org/signin/identifier"
    tabs: [{ title: "Sign in · Example Accounts", icon: "internet-web-browser" }]
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    addressRight: [
        ToolButton { icon.name: "dialog-password"; display: AbstractButton.IconOnly; flat: true; checked: true; implicitWidth: 28; implicitHeight: 28 }
    ]

    Rectangle {
        anchors.fill: parent
        color: "#ffffff"
        ColumnLayout {
            anchors.centerIn: parent
            width: 340
            spacing: 12
            Text { text: "Sign in"; font.pixelSize: 22; font.bold: true; color: "#232629"; Layout.alignment: Qt.AlignHCenter }
            Text { text: "Email or phone"; color: "#31363b" }
            Rectangle { Layout.fillWidth: true; height: 34; radius: 4; border.color: "#bdc3c7"; color: "#fcfcfc" }
            Rectangle { Layout.preferredWidth: 90; height: 36; radius: 4; color: "#3daee9"; Layout.alignment: Qt.AlignRight
                Text { anchors.centerIn: parent; text: "Next"; color: "white"; font.bold: true } }
        }
    }

    component AccountRow: ItemDelegate {
        id: row
        ToolTip.text: "Fill"
        ToolTip.delay: 600
        required property string username
        property bool passwordCopied: false
        Layout.fillWidth: true
        padding: Kirigami.Units.smallSpacing
        contentItem: RowLayout {
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Icon {
                source: "user-identity"
                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
            }
            Label { text: row.username; elide: Text.ElideRight; Layout.fillWidth: true }
            ToolButton {
                icon.name: "edit-copy"
                icon.width: Kirigami.Units.iconSizes.smallMedium
                icon.height: Kirigami.Units.iconSizes.smallMedium
                display: AbstractButton.IconOnly
                ToolTip.text: "Copy Username"
                Accessible.name: "Copy Username for " + row.username
            }
            ToolButton {
                icon.name: row.passwordCopied ? "dialog-ok-apply" : "password-copy"
                icon.color: row.passwordCopied ? Kirigami.Theme.positiveTextColor : "transparent"
                icon.width: Kirigami.Units.iconSizes.smallMedium
                icon.height: Kirigami.Units.iconSizes.smallMedium
                display: AbstractButton.IconOnly
                ToolTip.text: row.passwordCopied ? "Copied. Cleared in 30 seconds." : "Copy Password"
                Accessible.name: "Copy Password for " + row.username
            }
        }
    }

    Popup {
        popupType: Popup.Item
        x: 680
        y: -4
        width: 360
        padding: Kirigami.Units.largeSpacing
        Component.onCompleted: open()
        contentItem: ColumnLayout {
            spacing: Kirigami.Units.smallSpacing
            RowLayout {
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Icon { source: "dialog-password"; Layout.preferredWidth: 32; Layout.preferredHeight: 32 }
                ColumnLayout {
                    spacing: 0
                    Kirigami.Heading { level: 4; text: "Saved Passwords" }
                    Label { text: "accounts.example.org"; color: Kirigami.Theme.disabledTextColor }
                }
            }
            AccountRow { username: "maria@example.org"; passwordCopied: true }
            AccountRow { username: "maria.work@example.org" }
            AccountRow { username: "m.silva@example.org" }
            Kirigami.Separator { Layout.fillWidth: true }
            Button { text: "Manage Passwords…"; icon.name: "configure"; flat: true }
        }
    }

    ToolTip {
        popupType: Popup.Item
        x: 905
        y: 86
        text: "Copied. Cleared in 30 seconds."
        Component.onCompleted: open()
    }
}
