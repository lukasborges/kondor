// #14 Multiple windows — janela privada: ícone de navegação privada na barra de abas,
// todas as abas privadas e uma página de nova aba explicando o modo.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    privateWindow: true
    tabs: [{ title: "Nova aba privada", private: true }, { title: "Pesquisa — DuckDuckGo", private: true }]
    address: ""
    Rectangle {
        anchors.fill: parent
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor
        ColumnLayout {
            anchors.centerIn: parent
            width: 520
            spacing: Kirigami.Units.largeSpacing * 2
            Kirigami.Icon { source: "view-private"; Layout.preferredWidth: 96; Layout.preferredHeight: 96; Layout.alignment: Qt.AlignHCenter }
            Kirigami.Heading { level: 1; text: "Navegação privada"; Layout.alignment: Qt.AlignHCenter }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                text: "O Kondor não guarda histórico, cookies, dados de formulários nem permissões desta janela. Tudo é apagado quando você fecha a janela."
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                color: Kirigami.Theme.disabledTextColor
                text: "Downloads e favoritos que você criar continuam salvos. Seu provedor e os sites ainda podem ver sua atividade."
            }
        }
    }
}
