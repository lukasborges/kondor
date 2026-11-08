// #21 Password manager — pergunta para salvar a senha (InlineMessage) e chave na barra de endereço.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    address: "https://invent.kde.org/users/sign_in"
    tabs: [{ title: "Entrar · GitLab KDE", icon: "kde" }]
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
            text: "Salvar a senha de <b>maria</b> para <b>invent.kde.org</b> na carteira do KDE?"
            actions: [
                Kirigami.Action { text: "Salvar"; icon.name: "document-save" },
                Kirigami.Action { text: "Agora não"; icon.name: "dialog-cancel" },
                Kirigami.Action { text: "Nunca para este site"; icon.name: "edit-delete" }
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
            Text { text: "Entrar no GitLab KDE"; font.pixelSize: 22; font.bold: true; color: "#232629"; Layout.alignment: Qt.AlignHCenter }
            Text { text: "Usuário"; color: "#31363b" }
            Rectangle { Layout.fillWidth: true; height: 34; radius: 4; border.color: "#bdc3c7"; color: "#fcfcfc"
                Text { anchors.verticalCenter: parent.verticalCenter; x: 10; text: "maria"; color: "#232629" } }
            Text { text: "Senha"; color: "#31363b" }
            Rectangle { Layout.fillWidth: true; height: 34; radius: 4; border.color: "#bdc3c7"; color: "#fcfcfc"
                Text { anchors.verticalCenter: parent.verticalCenter; x: 10; text: "••••••••••"; color: "#232629" } }
            Rectangle { Layout.fillWidth: true; height: 36; radius: 4; color: "#3daee9"
                Text { anchors.centerIn: parent; text: "Entrar"; color: "white"; font.bold: true } }
        }
    }
}
