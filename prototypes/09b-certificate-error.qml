// #9 Certificate error — página sobreposta ao WebEngineView com "Voltar" e opção avançada.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    address: "https://expired.badssl.com/"
    tabs: [{ title: "Erro de privacidade", icon: "security-low" }]
    addressLeft: [
        ToolButton {
            icon.name: "security-low"; text: "Não seguro"
            display: AbstractButton.TextBesideIcon; flat: true; implicitHeight: 28
            icon.color: Kirigami.Theme.negativeTextColor
        }
    ]
    Rectangle {
        anchors.fill: parent
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor

        ColumnLayout {
            anchors.centerIn: parent
            width: 560
            spacing: Kirigami.Units.largeSpacing * 2
            Kirigami.Icon { source: "security-low"; Layout.preferredWidth: 96; Layout.preferredHeight: 96; Layout.alignment: Qt.AlignHCenter }
            Kirigami.Heading { level: 1; text: "Sua conexão não é segura"; Layout.alignment: Qt.AlignHCenter }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                text: "Invasores podem estar tentando roubar suas informações de <b>expired.badssl.com</b> (por exemplo, senhas, mensagens ou cartões de crédito)."
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                color: Kirigami.Theme.disabledTextColor
                text: "O certificado do servidor expirou. (ERR_CERT_DATE_INVALID)"
            }
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: Kirigami.Units.largeSpacing
                Button { text: "Avançado…"; flat: true; icon.name: "arrow-down" }
                Button { text: "Voltar para a segurança"; icon.name: "go-previous"; highlighted: true }
            }
            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: true
                type: Kirigami.MessageType.Warning
                text: "Este site não comprovou sua identidade. Continuar pode expor seus dados."
                actions: [ Kirigami.Action { text: "Continuar mesmo assim (não seguro)"; icon.name: "go-next" } ]
            }
        }
    }
}
