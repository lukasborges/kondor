// #21 Password manager — save-password prompt (InlineMessage) and key icon in the address bar.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    address: "https://invent.kde.org/users/sign_in"
    tabs: [{ title: "Sign in · KDE GitLab", icon: "kde" }]
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    addressRight: [
        ToolButton { icon.name: "dialog-password"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    belowHeader: [
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            position: Kirigami.InlineMessage.Position.Header
            visible: true
            type: Kirigami.MessageType.Information
            icon.name: "dialog-password"
            text: "Save the password for <b>maria</b> on <b>invent.kde.org</b> in KWallet?"
            actions: [
                Kirigami.Action { text: "Save"; icon.name: "document-save" },
                Kirigami.Action { text: "Not Now"; icon.name: "dialog-cancel" },
                Kirigami.Action { text: "Never for This Site"; icon.name: "edit-delete" }
            ]
        }
    ]
    Rectangle {
        anchors.fill: parent
        color: "#ffffff"
        ColumnLayout {
            anchors.centerIn: parent
            width: 340
            spacing: 12
            Kirigami.Icon { source: "kde"; Layout.preferredWidth: 56; Layout.preferredHeight: 56; Layout.alignment: Qt.AlignHCenter }
            Text { text: "Sign in to KDE GitLab"; font.pixelSize: 22; font.bold: true; color: "#232629"; Layout.alignment: Qt.AlignHCenter }
            Text { text: "Username"; color: "#31363b" }
            Rectangle { Layout.fillWidth: true; height: 34; radius: 4; border.color: "#bdc3c7"; color: "#fcfcfc"
                Text { anchors.verticalCenter: parent.verticalCenter; x: 10; text: "maria"; color: "#232629" } }
            Text { text: "Password"; color: "#31363b" }
            Rectangle { Layout.fillWidth: true; height: 34; radius: 4; border.color: "#bdc3c7"; color: "#fcfcfc"
                Text { anchors.verticalCenter: parent.verticalCenter; x: 10; text: "••••••••••"; color: "#232629" } }
            Rectangle { Layout.fillWidth: true; height: 36; radius: 4; color: "#3daee9"
                Text { anchors.centerIn: parent; text: "Sign in"; color: "white"; font.bold: true } }
        }
    }
}
