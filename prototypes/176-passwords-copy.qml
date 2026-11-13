// #176 Saved logins panel: click an account to fill, or copy its user name or password.
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
        required property string username
        Layout.fillWidth: true
        padding: Kirigami.Units.smallSpacing
        contentItem: RowLayout {
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Icon { source: "user-identity"; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
            Label { text: row.username; elide: Text.ElideRight; Layout.fillWidth: true }
            ToolButton { icon.name: "edit-copy"; display: AbstractButton.IconOnly; implicitWidth: 28; implicitHeight: 28 }
            ToolButton { icon.name: "password-copy"; display: AbstractButton.IconOnly; implicitWidth: 28; implicitHeight: 28 }
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
            Label {
                Layout.fillWidth: true
                Layout.topMargin: Kirigami.Units.smallSpacing
                wrapMode: Text.WordWrap
                color: Kirigami.Theme.disabledTextColor
                text: "Click an account to fill the page."
            }
            AccountRow { username: "maria@example.org" }
            AccountRow { username: "maria.work@example.org" }
            AccountRow { username: "m.silva@example.org" }
            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: true
                type: Kirigami.MessageType.Positive
                icon.name: "password-copy"
                text: "Password copied. It will be cleared from the clipboard in 30 seconds."
            }
            Kirigami.Separator { Layout.fillWidth: true }
            Button { text: "Manage Passwords…"; icon.name: "configure"; flat: true }
        }
    }
}
