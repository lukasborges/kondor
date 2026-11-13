// #176 Copy saved logins: "Copy Username" and "Copy Password" submenus in the Fill Saved Password menu.
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

    Menu {
        id: passwordMenu
        popupType: Popup.Item
        x: 800
        y: 0
        width: 260
        MenuItem { text: "maria@example.org"; icon.name: "user-identity" }
        MenuItem { text: "maria.work@example.org"; icon.name: "user-identity" }
        MenuSeparator {}
        Menu { id: copyUserRow; title: "Copy Username"; icon.name: "edit-copy"; popupType: Popup.Item }
        Menu { id: copyPasswordRow; title: "Copy Password"; icon.name: "edit-copy"; popupType: Popup.Item }
        Component.onCompleted: open()
    }

    SubmenuMock {
        id: copyPasswordMenu
        menuWidth: 240
        MenuItem { text: "maria@example.org"; icon.name: "user-identity"; highlighted: true }
        MenuItem { text: "maria.work@example.org"; icon.name: "user-identity" }
    }

    Timer {
        interval: 300
        running: true
        onTriggered: {
            const row = passwordMenu.itemAt(4)
            row.highlighted = true
            const local = row.mapToItem(passwordMenu.parent, 0, 0)
            copyPasswordMenu.parent = passwordMenu.parent
            copyPasswordMenu.x = passwordMenu.x - copyPasswordMenu.width + 4
            copyPasswordMenu.y = local.y - copyPasswordMenu.topPadding
            copyPasswordMenu.open()
        }
    }
}
